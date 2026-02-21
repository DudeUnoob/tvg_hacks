from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_services
from app.models.dispatch import DispatchRecommendation
from app.models.event import Event
from app.models.forecast import Forecast
from app.schemas.layer4 import ActiveDispatchResponse, DispatchResponse

router = APIRouter(prefix="/layer4", tags=["layer4"])


def _auto_sync_events_if_needed(services) -> None:
    if not services.settings.auto_sync_live_events:
        return
    if services.event_ingestion.list_events():
        return
    services.event_ingestion.sync_live_events(force=False)


def _ensure_forecast(event: Event, services) -> Forecast:
    crowd_signal = services.latest_signals.get(event.event_id)
    if crowd_signal is None:
        frames = services.frame_provider.get_frames(event=event, sample_size=3)
        crowd_signal = services.vlm_estimator.estimate(event=event, frames=frames)
        services.latest_signals[event.event_id] = crowd_signal

    forecast = services.crowd_fusion.build_forecast(event=event, crowd_signal=crowd_signal)
    services.latest_forecasts[event.event_id] = forecast
    return forecast


def _build_dispatch_for_event(event: Event, services) -> DispatchRecommendation:
    forecast = _ensure_forecast(event, services)
    weather = services.weather_service.get_weather_for_event(event)
    energy_profile = services.weather_service.get_event_energy_profile(
        event=event,
        temperature_override_f=weather.temperature_f,
    )
    wave = services.demand_wave_service.project_wave(
        event=event,
        adjusted_attendance=forecast.adjusted_attendance,
        weather_multiplier=energy_profile.weather_multiplier,
        venue_intensity_factor=energy_profile.venue_intensity_factor,
    )
    ercot = services.ercot_service.get_realtime_snapshot()
    recommendation = services.dispatch_engine.generate_recommendation(
        event=event,
        forecast=forecast,
        weather=weather,
        energy_profile=energy_profile,
        ercot=ercot,
        zip_projections=wave,
    )
    services.latest_dispatch[event.event_id] = recommendation
    return recommendation


@router.get("/dispatch/active", response_model=ActiveDispatchResponse)
def get_active_dispatch(services=Depends(get_services)) -> ActiveDispatchResponse:
    _auto_sync_events_if_needed(services)
    active_events = services.event_ingestion.list_active_events()
    if not active_events:
        active_events = services.event_ingestion.list_events()[:5]

    recommendations = [_build_dispatch_for_event(event=event, services=services) for event in active_events]
    recommendations = sorted(recommendations, key=lambda item: item.revenue_estimate_usd, reverse=True)
    return ActiveDispatchResponse(recommendations=recommendations)


@router.get("/dispatch/{event_id}", response_model=DispatchResponse)
def get_dispatch_for_event(event_id: str, services=Depends(get_services)) -> DispatchResponse:
    event = services.event_ingestion.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    recommendation = _build_dispatch_for_event(event=event, services=services)
    return DispatchResponse(recommendation=recommendation)
