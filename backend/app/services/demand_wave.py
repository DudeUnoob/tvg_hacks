from datetime import timedelta

from app.models.event import Event
from app.models.layer3 import ZipLoadProjection


class DemandWaveService:
    VENUE_ZIP_WEIGHTS: dict[str, list[tuple[str, float]]] = {
        "dkr": [("78705", 0.42), ("78751", 0.34), ("78752", 0.24)],
        "moody": [("78705", 0.36), ("78722", 0.33), ("78723", 0.31)],
        "cota": [("78617", 0.5), ("78725", 0.3), ("78744", 0.2)],
    }
    DEFAULT_ZIPS: list[tuple[str, float]] = [("78701", 0.4), ("78702", 0.35), ("78741", 0.25)]

    def project_wave(
        self,
        event: Event,
        adjusted_attendance: int,
        weather_multiplier: float,
        venue_intensity_factor: float = 1.0,
    ) -> list[ZipLoadProjection]:
        zip_weights = self._resolve_zip_weights(event.venue)
        base_kw_per_person = 0.0033
        total_delta_mw = (
            adjusted_attendance * base_kw_per_person * weather_multiplier * venue_intensity_factor
        ) / 1000.0

        projections: list[ZipLoadProjection] = []
        for index, (zip_code, weight) in enumerate(zip_weights):
            projections.append(
                ZipLoadProjection(
                    zip_code=zip_code,
                    projected_load_delta_mw=round(max(total_delta_mw * weight, 0.0), 4),
                    share_of_wave_pct=round(weight, 4),
                    peak_time=event.projected_dispersal_peak + timedelta(minutes=index * 8),
                )
            )
        return projections

    @staticmethod
    def peak_mw(projections: list[ZipLoadProjection]) -> float:
        return round(sum(item.projected_load_delta_mw for item in projections), 4)

    def _resolve_zip_weights(self, venue: str) -> list[tuple[str, float]]:
        normalized = venue.strip().lower()
        for key, weights in self.VENUE_ZIP_WEIGHTS.items():
            if key in normalized:
                return weights
        return self.DEFAULT_ZIPS
