import pytest

from app.config import Settings
from app.services.energy_lookup import EnergyLookupService


def _build_service() -> EnergyLookupService:
    return EnergyLookupService(
        Settings(
            energy_lookup_enabled=True,
            comprehensive_energy_lookup_csv_path="data/comprehensive_energy_lookup_5deg.csv",
        )
    )


def test_energy_lookup_loads_csv_and_median() -> None:
    service = _build_service()
    profile = service.get_profile("Moody Center", 65)

    assert service.loaded_venue_count >= 10
    assert service.base_kwh_median > 0
    assert profile.source == "comprehensive_csv"
    assert profile.matched_venue == "Moody Center"
    assert profile.base_kwh == pytest.approx(43561.64)
    assert profile.interpolated_kwh == pytest.approx(43561.64)
    assert profile.weather_multiplier == pytest.approx(1.0)


def test_energy_lookup_interpolates_non_bin_temperature() -> None:
    service = _build_service()
    profile = service.get_profile("Moody Center", 82.5)

    expected_kwh = 46175.34 + ((47482.19 - 46175.34) * 0.5)
    expected_multiplier = expected_kwh / 43561.64

    assert profile.lower_bin_f == 80
    assert profile.upper_bin_f == 85
    assert profile.interpolated_kwh == pytest.approx(expected_kwh, rel=1e-4)
    assert profile.weather_multiplier == pytest.approx(expected_multiplier, rel=1e-4)


def test_energy_lookup_uses_alias_mapping_for_known_venues() -> None:
    service = _build_service()
    profile = service.get_profile("Lee and Joe Jamail Texas Swimming Center", 70)

    assert profile.source == "comprehensive_csv"
    assert profile.matched_venue == "Lee and Joe Jamail Swimming Center"
    assert profile.base_kwh == pytest.approx(12842.38)
    assert profile.weather_multiplier == pytest.approx(1.035, rel=0.1)


def test_energy_lookup_falls_back_for_unknown_venue() -> None:
    service = _build_service()
    profile = service.get_profile("Unknown Venue", 200)

    assert profile.source == "fallback_curve"
    assert profile.matched_venue is None
    assert profile.temperature_f == 115
    assert profile.interpolated_kwh is None
    assert profile.base_kwh is None
    assert profile.weather_multiplier == pytest.approx(1.42)
    assert profile.venue_intensity_factor == pytest.approx(1.0)
