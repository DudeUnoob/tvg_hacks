from dataclasses import dataclass, field

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.crowd import router as crowd_router
from app.api.events import router as events_router
from app.api.forecasts import router as forecasts_router
from app.api.layer3 import router as layer3_router
from app.api.layer4 import router as layer4_router
from app.config import Settings, get_settings
from app.models.crowd_signal import CrowdSignal
from app.models.dispatch import DispatchRecommendation
from app.models.forecast import Forecast
from app.services.crowd_fusion import CrowdFusionService
from app.services.demand_wave import DemandWaveService
from app.services.dispatch_engine import DispatchEngine
from app.services.energy_lookup import EnergyLookupService
from app.services.ercot_service import ErcotService
from app.services.event_ingestion import (
    CsvSportsEventsAdapter,
    EventIngestionService,
    LocalistEventsAdapter,
    MoodyCenterWebAdapter,
    TicketmasterDiscoveryAdapter,
)
from app.services.frame_provider import MockFrameProvider
from app.services.urban_planning import UrbanPlanningService
from app.services.vlm_gemini import GeminiCrowdEstimator
from app.services.weather_service import WeatherService


@dataclass
class ServiceContainer:
    settings: Settings
    event_ingestion: EventIngestionService
    frame_provider: MockFrameProvider
    vlm_estimator: GeminiCrowdEstimator
    crowd_fusion: CrowdFusionService
    energy_lookup_service: EnergyLookupService
    weather_service: WeatherService
    ercot_service: ErcotService
    demand_wave_service: DemandWaveService
    urban_planning_service: UrbanPlanningService
    dispatch_engine: DispatchEngine
    latest_signals: dict[str, CrowdSignal] = field(default_factory=dict)
    latest_forecasts: dict[str, Forecast] = field(default_factory=dict)
    latest_dispatch: dict[str, DispatchRecommendation] = field(default_factory=dict)


def build_services(settings: Settings) -> ServiceContainer:
    live_adapters = []
    if settings.csv_events_enabled and settings.ut_sports_csv_path:
        live_adapters.append(
            CsvSportsEventsAdapter(
                events_csv_path=settings.ut_sports_csv_path,
                venues_capacity_csv_path=settings.venues_capacity_csv_path,
                facility_energy_csv_path=settings.facility_energy_csv_path,
            )
        )
    live_adapters.extend(
        [
            LocalistEventsAdapter(
                api_url=settings.ut_localist_api_url,
                source_name="ut_localist_dkr",
                search_term="Darrell K Royal",
                results_per_page=settings.localist_results_per_page,
                keyword_filters=["darrell", "stadium", "football", "longhorns"],
            ),
            LocalistEventsAdapter(
                api_url=settings.ut_localist_api_url,
                source_name="ut_localist_moody",
                search_term="Moody Center",
                results_per_page=settings.localist_results_per_page,
                keyword_filters=["moody", "basketball", "concert", "spurs", "longhorns"],
            ),
            MoodyCenterWebAdapter(events_url=settings.moody_events_url),
        ]
    )
    if settings.ticketmaster_api_key:
        live_adapters.append(
            TicketmasterDiscoveryAdapter(
                api_url=settings.ticketmaster_api_url,
                api_key=settings.ticketmaster_api_key,
            )
        )

    energy_lookup_service = EnergyLookupService(settings=settings)

    return ServiceContainer(
        settings=settings,
        event_ingestion=EventIngestionService(
            default_radius_meters=settings.default_event_radius_meters,
            live_sync_interval_seconds=settings.live_event_sync_interval_seconds,
            live_adapters=live_adapters,
        ),
        frame_provider=MockFrameProvider(settings=settings),
        vlm_estimator=GeminiCrowdEstimator(settings=settings),
        crowd_fusion=CrowdFusionService(),
        energy_lookup_service=energy_lookup_service,
        weather_service=WeatherService(settings=settings, energy_lookup_service=energy_lookup_service),
        ercot_service=ErcotService(settings=settings),
        demand_wave_service=DemandWaveService(),
        urban_planning_service=UrbanPlanningService(),
        dispatch_engine=DispatchEngine(settings=settings),
    )


def _parse_cors_origins(raw_origins: str) -> list[str]:
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return origins or ["*"]


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(title=resolved_settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_parse_cors_origins(resolved_settings.cors_allowed_origins),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.services = build_services(resolved_settings)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "env": resolved_settings.app_env}

    app.include_router(events_router)
    app.include_router(crowd_router)
    app.include_router(forecasts_router)
    app.include_router(layer3_router)
    app.include_router(layer4_router)
    return app


app = create_app()
