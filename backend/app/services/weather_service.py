import hashlib
from datetime import datetime, timezone

from app.config import Settings
from app.models.event import Event
from app.models.layer3 import WeatherSnapshot


class WeatherService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def get_current_weather(self, latitude: float, longitude: float) -> WeatherSnapshot:
        if self.settings.weather_source != "mock":
            # MVP uses deterministic mock weather. Real adapter can be added behind this branch.
            pass

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

    def get_weather_for_event(self, event: Event, temperature_override_f: float | None = None) -> WeatherSnapshot:
        if temperature_override_f is not None:
            snapshot = self.get_current_weather(event.latitude, event.longitude)
            snapshot.temperature_f = round(temperature_override_f, 1)
            snapshot.condition = "extreme-heat" if snapshot.temperature_f >= 100 else snapshot.condition
            return snapshot
        return self.get_current_weather(event.latitude, event.longitude)

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
