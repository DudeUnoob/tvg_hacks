from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GridPulse Layer1-Layer2 API"
    app_env: str = "dev"
    mock_mode: bool = True

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"

    ut_calendar_url: str | None = None
    txdot_camera_catalog_url: str | None = None

    mock_empty_frames: bool = False
    mock_frame_count: int = Field(default=5, ge=0, le=20)
    default_event_radius_meters: int = Field(default=2500, ge=200, le=20000)

    model_config = SettingsConfigDict(
        env_prefix="GRIDPULSE_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
