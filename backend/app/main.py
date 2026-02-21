from dataclasses import dataclass, field

from fastapi import FastAPI

from app.api.crowd import router as crowd_router
from app.api.events import router as events_router
from app.api.forecasts import router as forecasts_router
from app.config import Settings, get_settings
from app.models.crowd_signal import CrowdSignal
from app.models.forecast import Forecast
from app.services.crowd_fusion import CrowdFusionService
from app.services.event_ingestion import EventIngestionService
from app.services.frame_provider import MockFrameProvider
from app.services.vlm_gemini import GeminiCrowdEstimator


@dataclass
class ServiceContainer:
    settings: Settings
    event_ingestion: EventIngestionService
    frame_provider: MockFrameProvider
    vlm_estimator: GeminiCrowdEstimator
    crowd_fusion: CrowdFusionService
    latest_signals: dict[str, CrowdSignal] = field(default_factory=dict)
    latest_forecasts: dict[str, Forecast] = field(default_factory=dict)


def build_services(settings: Settings) -> ServiceContainer:
    return ServiceContainer(
        settings=settings,
        event_ingestion=EventIngestionService(default_radius_meters=settings.default_event_radius_meters),
        frame_provider=MockFrameProvider(settings=settings),
        vlm_estimator=GeminiCrowdEstimator(settings=settings),
        crowd_fusion=CrowdFusionService(),
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(title=resolved_settings.app_name, version="0.1.0")
    app.state.services = build_services(resolved_settings)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "env": resolved_settings.app_env}

    app.include_router(events_router)
    app.include_router(crowd_router)
    app.include_router(forecasts_router)
    return app


app = create_app()
