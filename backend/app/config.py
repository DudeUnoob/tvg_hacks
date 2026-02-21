from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GridPulse Layer1-Layer4 API"
    app_env: str = "dev"
    mock_mode: bool = True

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"

    ut_calendar_url: str | None = None
    txdot_camera_catalog_url: str | None = None

    mock_empty_frames: bool = False
    mock_frame_count: int = Field(default=5, ge=0, le=20)
    default_event_radius_meters: int = Field(default=2500, ge=200, le=20000)
    default_worst_case_temp_f: float = Field(default=102.0, ge=90.0, le=110.0)

    weather_source: str = "mock"
    weather_api_key: str | None = None
    weather_mock_temperature_f: float = Field(default=91.0, ge=50.0, le=120.0)

    ercot_source: str = "mock"
    ercot_mock_price_mwh: float = Field(default=285.0, ge=0.0)
    ercot_mock_load_mw: float = Field(default=47200.0, ge=0.0)

    urban_data_source: str = "mock"
    dispatch_precharge_hours: int = Field(default=2, ge=1, le=8)
    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_prefix="GRIDPULSE_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
