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
from app.services.ercot_service import ErcotService
from app.services.event_ingestion import EventIngestionService
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
    weather_service: WeatherService
    ercot_service: ErcotService
    demand_wave_service: DemandWaveService
    urban_planning_service: UrbanPlanningService
    dispatch_engine: DispatchEngine
    latest_signals: dict[str, CrowdSignal] = field(default_factory=dict)
    latest_forecasts: dict[str, Forecast] = field(default_factory=dict)
    latest_dispatch: dict[str, DispatchRecommendation] = field(default_factory=dict)


def build_services(settings: Settings) -> ServiceContainer:
    return ServiceContainer(
        settings=settings,
        event_ingestion=EventIngestionService(default_radius_meters=settings.default_event_radius_meters),
        frame_provider=MockFrameProvider(settings=settings),
        vlm_estimator=GeminiCrowdEstimator(settings=settings),
        crowd_fusion=CrowdFusionService(),
        weather_service=WeatherService(settings=settings),
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
