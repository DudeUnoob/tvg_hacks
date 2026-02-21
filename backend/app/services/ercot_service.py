from datetime import datetime, timezone

from app.config import Settings
from app.models.layer3 import ErcotSnapshot


class ErcotService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def get_realtime_snapshot(self) -> ErcotSnapshot:
        if self.settings.ercot_source != "mock":
            # MVP uses deterministic mock ERCOT data.
            pass

        now = datetime.now(timezone.utc)
        hour_mod = (now.hour % 6) * 0.03
        price = self.settings.ercot_mock_price_mwh * (1.0 + hour_mod)
        load = self.settings.ercot_mock_load_mw * (1.0 + (hour_mod / 2.0))
        return ErcotSnapshot(
            price_mwh=round(price, 2),
            load_mw=round(load, 1),
            source="mock",
            updated_at=now,
        )

    @staticmethod
    def comparable_signal(temperature_f: float, adjusted_attendance: int) -> str:
        if temperature_f >= 100 and adjusted_attendance >= 90_000:
            return "Historical profile: major game + extreme heat demand spike"
        if adjusted_attendance >= 40_000:
            return "Historical profile: major event return-home surge"
        return "Historical profile: medium event evening recovery wave"
