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
    ut_localist_api_url: str = "https://calendar.utexas.edu/api/2/events"
    moody_events_url: str = "https://moodycenteratx.com/events/"
    ticketmaster_api_key: str | None = None
    ticketmaster_api_url: str = "https://app.ticketmaster.com/discovery/v2/events.json"
    live_event_sync_interval_seconds: int = Field(default=300, ge=30, le=3600)
    auto_sync_live_events: bool = True
    csv_events_enabled: bool = True
    ut_sports_csv_path: str | None = "data/UT_Sports_Events.csv"
    venues_capacity_csv_path: str | None = "data/venues_capacity.csv"
    facility_energy_csv_path: str | None = "data/Facility_Energy_Usage.csv"
    comprehensive_energy_lookup_csv_path: str | None = "data/comprehensive_energy_lookup_5deg.csv"
    energy_lookup_enabled: bool = True
    localist_results_per_page: int = Field(default=60, ge=10, le=200)
    txdot_camera_catalog_url: str | None = None
    camera_catalog_refresh_seconds: int = Field(default=600, ge=60, le=3600)

    mock_empty_frames: bool = False
    mock_frame_count: int = Field(default=5, ge=0, le=20)
    default_event_radius_meters: int = Field(default=2500, ge=200, le=20000)
    default_worst_case_temp_f: float = Field(default=102.0, ge=90.0, le=110.0)

    weather_source: str = "open_meteo"
    weather_api_key: str | None = None
    weather_mock_temperature_f: float = Field(default=91.0, ge=50.0, le=120.0)

    ercot_source: str = "ercot_public_api"
    ercot_public_base_url: str = "https://www.ercot.com/api/1/services/read/dashboards"
    ercot_api_base_url: str = "https://api.ercot.com"
    ercot_public_reports_path: str = "/api/public-reports"
    ercot_public_emil_id: str = "NP6-905-CD"
    ercot_public_operation: str = "2d_agg_edc"
    ercot_subscription_key: str | None = None
    ercot_subscription_secondary_key: str | None = None
    ercot_id_token: str | None = None
    ercot_endpoint_discovery: bool = True
    ercot_use_legacy_dashboard_fallback: bool = False
    ercot_api_timeout_seconds: float = Field(default=10.0, ge=2.0, le=30.0)
    eia_api_key: str = "DEMO_KEY"
    ercot_refresh_seconds: int = Field(default=300, ge=30, le=1800)
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
