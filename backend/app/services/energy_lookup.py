import csv
from dataclasses import dataclass
from pathlib import Path
import re
from statistics import median

from app.config import Settings
from app.models.energy import VenueEnergyProfile


@dataclass(frozen=True)
class _VenueCurve:
    venue: str
    base_kwh: float
    bins: dict[int, float]


class EnergyLookupService:
    _temperature_column = re.compile(r"^(\d+)F$", re.IGNORECASE)
    _default_min_temp_f = 20.0
    _default_max_temp_f = 115.0

    _alias_map: dict[str, str] = {
        "Lee and Joe Jamail Texas Swimming Center": "Lee and Joe Jamail Swimming Center",
        "Mike A. Myers Stadium and Soccer Field": "Mike A. Myers Stadium",
    }

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.enabled = settings.energy_lookup_enabled
        self.lookup_csv_path = settings.comprehensive_energy_lookup_csv_path
        self.facility_energy_csv_path = settings.facility_energy_csv_path

        self._curves: dict[str, _VenueCurve] = {}
        self._base_kwh_median: float = 0.0
        self._min_temp_f = self._default_min_temp_f
        self._max_temp_f = self._default_max_temp_f
        self._facility_intensity_factors: dict[str, float] = {}
        self._aliases_normalized = {
            self._normalize_venue(raw_key): self._normalize_venue(raw_value)
            for raw_key, raw_value in self._alias_map.items()
        }
        self._reverse_aliases_normalized = {
            value: key for key, value in self._aliases_normalized.items()
        }
        self._load_csv()
        self._load_facility_energy_index()

    @property
    def loaded_venue_count(self) -> int:
        return len(self._curves)

    @property
    def base_kwh_median(self) -> float:
        return self._base_kwh_median

    def get_profile(self, venue: str, temperature_f: float) -> VenueEnergyProfile:
        temperature_clamped = self._clamp_temperature_f(temperature_f)
        if not self.enabled:
            return self._build_fallback_profile(venue=venue, temperature_f=temperature_clamped)

        curve = self._match_curve(venue)
        if curve is None:
            return self._build_fallback_profile(venue=venue, temperature_f=temperature_clamped)

        lower_bin_f, upper_bin_f, interpolated_kwh = self._interpolate(curve=curve, temperature_f=temperature_clamped)
        base_kwh = max(curve.base_kwh, 0.0)
        weather_multiplier = (interpolated_kwh / base_kwh) if base_kwh > 0 else 1.0
        venue_intensity_factor = self._resolve_venue_intensity_factor(
            requested_venue=venue,
            matched_venue=curve.venue,
            base_kwh=base_kwh,
        )

        return VenueEnergyProfile(
            requested_venue=venue,
            matched_venue=curve.venue,
            source="comprehensive_csv",
            temperature_f=round(temperature_clamped, 3),
            lower_bin_f=lower_bin_f,
            upper_bin_f=upper_bin_f,
            interpolated_kwh=round(max(interpolated_kwh, 0.0), 4),
            base_kwh=round(base_kwh, 4),
            weather_multiplier=round(max(weather_multiplier, 0.0), 6),
            venue_intensity_factor=round(max(venue_intensity_factor, 0.0), 6),
        )

    def _load_csv(self) -> None:
        path = self._resolve_path(self.lookup_csv_path)
        if path is None or not path.exists():
            return

        loaded_curves: dict[str, _VenueCurve] = {}
        base_values: list[float] = []
        all_bins: set[int] = set()

        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                venue = str(row.get("Venue") or "").strip()
                base_kwh = self._to_float(row.get("Base_kWh"))
                if not venue or base_kwh is None:
                    continue

                bins: dict[int, float] = {}
                for key, raw_value in row.items():
                    if key is None:
                        continue
                    match = self._temperature_column.match(key.strip())
                    if not match:
                        continue
                    bin_value = self._to_float(raw_value)
                    if bin_value is None:
                        continue
                    bin_f = int(match.group(1))
                    bins[bin_f] = bin_value
                    all_bins.add(bin_f)

                if not bins:
                    continue

                normalized_venue = self._normalize_venue(venue)
                resolved_base = base_kwh if base_kwh > 0 else bins[min(bins.keys())]
                loaded_curves[normalized_venue] = _VenueCurve(venue=venue, base_kwh=resolved_base, bins=bins)
                base_values.append(resolved_base)

        self._curves = loaded_curves
        if base_values:
            self._base_kwh_median = float(median(base_values))
        if all_bins:
            self._min_temp_f = float(min(all_bins))
            self._max_temp_f = float(max(all_bins))

    def _load_facility_energy_index(self) -> None:
        path = self._resolve_path(self.facility_energy_csv_path)
        if path is None or not path.exists():
            return

        usage_map: dict[str, float] = {}
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                venue = str(row.get("Center Name") or row.get("Venue") or "").strip()
                usage = self._to_float(row.get("Energy Usage"))
                if not venue or usage is None:
                    continue
                usage_map[self._normalize_venue(venue)] = usage

        if not usage_map:
            return

        usage_values = list(usage_map.values())
        usage_min = min(usage_values)
        usage_max = max(usage_values)

        self._facility_intensity_factors = {
            venue_key: self._usage_to_intensity_factor(usage=usage, usage_min=usage_min, usage_max=usage_max)
            for venue_key, usage in usage_map.items()
        }

    @staticmethod
    def _resolve_path(path_value: str | None) -> Path | None:
        if not path_value:
            return None
        candidate = Path(path_value).expanduser()
        if candidate.exists():
            return candidate
        backend_root = Path(__file__).resolve().parents[2]
        backend_candidate = backend_root / candidate
        if backend_candidate.exists():
            return backend_candidate
        repo_candidate = backend_root.parent / candidate
        if repo_candidate.exists():
            return repo_candidate
        return candidate

    def _match_curve(self, venue: str) -> _VenueCurve | None:
        candidates = self._candidate_venue_keys(venue)
        if not candidates:
            return None

        for candidate in candidates:
            curve = self._curves.get(candidate)
            if curve is not None:
                return curve

        best_match_key: str | None = None
        best_score = 10_000
        for candidate in candidates:
            for key in self._curves:
                if candidate in key or key in candidate:
                    score = abs(len(candidate) - len(key))
                    if score < best_score:
                        best_score = score
                        best_match_key = key
        if best_match_key is not None:
            return self._curves[best_match_key]
        return None

    def _resolve_venue_intensity_factor(self, requested_venue: str, matched_venue: str | None, base_kwh: float) -> float:
        if matched_venue:
            matched_factor = self._match_facility_intensity(matched_venue)
            if matched_factor is not None:
                return matched_factor

        requested_factor = self._match_facility_intensity(requested_venue)
        if requested_factor is not None:
            return requested_factor

        return (base_kwh / self._base_kwh_median) if self._base_kwh_median > 0 else 1.0

    def _match_facility_intensity(self, venue: str) -> float | None:
        if not self._facility_intensity_factors:
            return None

        candidates = self._candidate_venue_keys(venue)
        for candidate in candidates:
            factor = self._facility_intensity_factors.get(candidate)
            if factor is not None:
                return factor

        best_match_key: str | None = None
        best_score = 10_000
        for candidate in candidates:
            for key in self._facility_intensity_factors:
                if candidate in key or key in candidate:
                    score = abs(len(candidate) - len(key))
                    if score < best_score:
                        best_score = score
                        best_match_key = key
        if best_match_key is not None:
            return self._facility_intensity_factors[best_match_key]
        return None

    def _candidate_venue_keys(self, venue: str) -> list[str]:
        normalized = self._normalize_venue(venue)
        if not normalized:
            return []

        candidates = [normalized]
        alias = self._aliases_normalized.get(normalized)
        if alias and alias not in candidates:
            candidates.insert(0, alias)
        reverse_alias = self._reverse_aliases_normalized.get(normalized)
        if reverse_alias and reverse_alias not in candidates:
            candidates.insert(0, reverse_alias)
        return candidates

    def _interpolate(self, curve: _VenueCurve, temperature_f: float) -> tuple[int, int, float]:
        bins_sorted = sorted(curve.bins.keys())
        if not bins_sorted:
            fallback = max(curve.base_kwh, 0.0)
            return int(self._min_temp_f), int(self._max_temp_f), fallback

        if temperature_f <= bins_sorted[0]:
            first_bin = bins_sorted[0]
            return first_bin, first_bin, curve.bins[first_bin]
        if temperature_f >= bins_sorted[-1]:
            last_bin = bins_sorted[-1]
            return last_bin, last_bin, curve.bins[last_bin]

        for index in range(len(bins_sorted) - 1):
            lower = bins_sorted[index]
            upper = bins_sorted[index + 1]
            if lower <= temperature_f <= upper:
                if lower == upper:
                    return lower, upper, curve.bins[lower]
                lower_value = curve.bins[lower]
                upper_value = curve.bins[upper]
                ratio = (temperature_f - lower) / (upper - lower)
                interpolated = lower_value + ((upper_value - lower_value) * ratio)
                return lower, upper, interpolated

        last_bin = bins_sorted[-1]
        return last_bin, last_bin, curve.bins[last_bin]

    def _build_fallback_profile(self, venue: str, temperature_f: float) -> VenueEnergyProfile:
        return VenueEnergyProfile(
            requested_venue=venue,
            matched_venue=None,
            source="fallback_curve",
            temperature_f=round(temperature_f, 3),
            lower_bin_f=None,
            upper_bin_f=None,
            interpolated_kwh=None,
            base_kwh=None,
            weather_multiplier=self._fallback_weather_multiplier(temperature_f),
            venue_intensity_factor=1.0,
        )

    def _clamp_temperature_f(self, temperature_f: float) -> float:
        return max(self._min_temp_f, min(self._max_temp_f, float(temperature_f)))

    @staticmethod
    def _normalize_venue(value: str) -> str:
        lowered = value.lower().replace("&", " and ")
        cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
        return re.sub(r"\s+", " ", cleaned).strip()

    @staticmethod
    def _to_float(value: object) -> float | None:
        try:
            if value is None:
                return None
            return float(str(value).strip())
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _usage_to_intensity_factor(usage: float, usage_min: float, usage_max: float) -> float:
        if usage_max <= usage_min:
            return 1.0
        normalized = (usage - usage_min) / (usage_max - usage_min)
        bounded = max(0.0, min(normalized, 1.0))
        return 0.6 + (bounded * 1.2)

    @staticmethod
    def _fallback_weather_multiplier(temperature_f: float) -> float:
        if temperature_f <= 60:
            return 0.72
        if temperature_f <= 75:
            return 0.9
        if temperature_f <= 90:
            return 1.08
        if temperature_f <= 100:
            return 1.28
        return 1.42
