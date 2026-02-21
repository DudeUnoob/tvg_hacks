from datetime import timedelta

from app.config import Settings
from app.models.dispatch import DispatchRecommendation, DispatchTarget
from app.models.energy import VenueEnergyProfile
from app.models.event import Event
from app.models.forecast import Forecast
from app.models.layer3 import ErcotSnapshot, WeatherSnapshot, ZipLoadProjection
from app.services.ercot_service import ErcotService


class DispatchEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_recommendation(
        self,
        event: Event,
        forecast: Forecast,
        weather: WeatherSnapshot,
        energy_profile: VenueEnergyProfile,
        ercot: ErcotSnapshot,
        zip_projections: list[ZipLoadProjection],
    ) -> DispatchRecommendation:
        ranked = sorted(zip_projections, key=lambda item: item.projected_load_delta_mw, reverse=True)
        targets: list[DispatchTarget] = []

        for index, item in enumerate(ranked[:3]):
            recommended_capacity_pct = min(0.95, max(0.28, 0.42 + (item.projected_load_delta_mw * 9.0)))
            estimated_battery_count = int(round((item.projected_load_delta_mw * 1000.0) / 5.2))
            targets.append(
                DispatchTarget(
                    rank=index + 1,
                    zip_code=item.zip_code,
                    recommended_capacity_pct=round(recommended_capacity_pct, 4),
                    projected_load_delta_mw=item.projected_load_delta_mw,
                    estimated_battery_count=max(estimated_battery_count, 0),
                )
            )

        spread_mw = sum(target.projected_load_delta_mw for target in targets)
        revenue_estimate_usd = round(max(ercot.price_mwh - 95.0, 20.0) * spread_mw * 165.0, 2)
        lead_hours = self.settings.dispatch_precharge_hours
        precharge_start = event.projected_dispersal_peak - timedelta(hours=lead_hours)
        comparable = ErcotService.comparable_signal(weather.temperature_f, forecast.adjusted_attendance)

        reasoning = (
            f"{event.name}: attendance {forecast.adjusted_attendance} with "
            f"{forecast.confidence * 100:.1f}% confidence. Temp {weather.temperature_f:.1f}F. "
            f"{comparable}. Energy lookup: {energy_profile.source} "
            f"(matched venue: {energy_profile.matched_venue or 'unmatched'}, "
            f"weather multiplier: {energy_profile.weather_multiplier:.3f}, "
            f"venue intensity: {energy_profile.venue_intensity_factor:.3f}). "
            f"Prioritize zip codes {', '.join(target.zip_code for target in targets)} "
            f"starting {lead_hours}h before dispersal peak."
        )

        return DispatchRecommendation(
            event_id=event.event_id,
            event_name=event.name,
            generated_at=ercot.updated_at,
            precharge_start_time=precharge_start,
            lead_time_hours=lead_hours,
            confidence=forecast.confidence,
            temperature_f=weather.temperature_f,
            weather_multiplier=energy_profile.weather_multiplier,
            revenue_estimate_usd=revenue_estimate_usd,
            comparable_signal=comparable,
            reasoning_trace=reasoning,
            energy_profile=energy_profile,
            targets=targets,
        )
