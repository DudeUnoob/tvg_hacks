import hashlib
from datetime import datetime, timezone

import httpx

from app.config import Settings
from app.models.energy import VenueEnergyProfile
from app.models.event import Event
from app.models.layer3 import WeatherSnapshot
from app.services.energy_lookup import EnergyLookupService


class WeatherService:
    def __init__(self, settings: Settings, energy_lookup_service: EnergyLookupService) -> None:
        self.settings = settings
        self.energy_lookup_service = energy_lookup_service

    def get_current_weather(self, latitude: float, longitude: float) -> WeatherSnapshot:
        if self.settings.weather_source in {"open_meteo", "live"}:
            live = self._get_open_meteo_weather(latitude=latitude, longitude=longitude)
            if live is not None:
                return live

        seed_input = f"{latitude:.4f}:{longitude:.4f}:{datetime.now(timezone.utc).hour}"
        digest = hashlib.sha256(seed_input.encode()).hexdigest()
        offset = (int(digest[:2], 16) / 255.0) * 12.0 - 6.0
        humidity_offset = (int(digest[2:4], 16) / 255.0) * 14.0 - 7.0
        temperature_f = round(self.settings.weather_mock_temperature_f + offset, 1)
        humidity_pct = max(22.0, min(88.0, 54.0 + humidity_offset))
        condition = "clear" if temperature_f < 95 else "hot"

        return WeatherSnapshot(
            temperature_f=temperature_f,
            humidity_pct=round(humidity_pct, 1),
            condition=condition,
            source="mock",
            observed_at=datetime.now(timezone.utc),
        )

    def _get_open_meteo_weather(self, latitude: float, longitude: float) -> WeatherSnapshot | None:
        params = {
            "latitude": f"{latitude:.4f}",
            "longitude": f"{longitude:.4f}",
            "current": "temperature_2m,relative_humidity_2m,weather_code",
            "temperature_unit": "fahrenheit",
        }
        try:
            with httpx.Client(timeout=8.0) as client:
                response = client.get("https://api.open-meteo.com/v1/forecast", params=params)
                response.raise_for_status()
                body = response.json()
            current = body.get("current") or {}
            temperature = float(current["temperature_2m"])
            humidity = float(current["relative_humidity_2m"])
            weather_code = int(current.get("weather_code", 0))
            observed_raw = datetime.fromisoformat(str(current.get("time", "")).replace("Z", "+00:00"))
            observed_at = (
                observed_raw.replace(tzinfo=timezone.utc)
                if observed_raw.tzinfo is None
                else observed_raw.astimezone(timezone.utc)
            )
            return WeatherSnapshot(
                temperature_f=round(temperature, 1),
                humidity_pct=round(max(min(humidity, 100.0), 0.0), 1),
                condition=self._condition_from_weather_code(weather_code),
                source="open-meteo",
                observed_at=observed_at,
            )
        except Exception:
            return None

    @staticmethod
    def _condition_from_weather_code(weather_code: int) -> str:
        if weather_code in {0, 1}:
            return "clear"
        if weather_code in {2, 3}:
            return "cloudy"
        if weather_code in {45, 48}:
            return "fog"
        if weather_code in {51, 53, 55, 61, 63, 65, 80, 81, 82}:
            return "rain"
        if weather_code in {71, 73, 75, 77, 85, 86}:
            return "snow"
        if weather_code in {95, 96, 99}:
            return "storm"
        return "variable"

    def get_weather_for_event(self, event: Event, temperature_override_f: float | None = None) -> WeatherSnapshot:
        if temperature_override_f is not None:
            snapshot = self.get_current_weather(event.latitude, event.longitude)
            snapshot.temperature_f = round(temperature_override_f, 1)
            snapshot.condition = "extreme-heat" if snapshot.temperature_f >= 100 else snapshot.condition
            return snapshot
        return self.get_current_weather(event.latitude, event.longitude)

    def get_event_energy_profile(
        self,
        event: Event,
        temperature_override_f: float | None = None,
    ) -> VenueEnergyProfile:
        if temperature_override_f is None:
            weather = self.get_weather_for_event(event)
            temperature_f = weather.temperature_f
        else:
            temperature_f = float(temperature_override_f)

        profile = self.energy_lookup_service.get_profile(event.venue, temperature_f=temperature_f)
        if profile.source == "fallback_curve":
            return profile.model_copy(
                update={
                    "weather_multiplier": self.compute_load_multiplier(profile.temperature_f),
                    "venue_intensity_factor": 1.0,
                }
            )
        return profile

    @staticmethod
    def compute_load_multiplier(temperature_f: float) -> float:
        if temperature_f <= 60:
            return 0.72
        if temperature_f <= 75:
            return 0.9
        if temperature_f <= 90:
            return 1.08
        if temperature_f <= 100:
            return 1.28
        return 1.42
