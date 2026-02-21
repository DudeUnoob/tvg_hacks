from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_services
from app.models.event import Event
from app.models.forecast import Forecast
from app.models.layer3 import MapEventState
from app.schemas.forecast import ForecastResponse
from app.schemas.layer3 import (
    MapStateResponse,
    UrbanOverlaysResponse,
    UrbanSimulationRequest,
    UrbanSimulationResponse,
    WeatherSimulationRequest,
    WeatherSimulationResponse,
)

router = APIRouter(prefix="/layer3", tags=["layer3"])


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


@router.get("/map-state", response_model=MapStateResponse)
def get_map_state(services=Depends(get_services)) -> MapStateResponse:
    _auto_sync_events_if_needed(services)
    events = services.event_ingestion.list_active_events()
    if not events:
        events = services.event_ingestion.list_events()[:5]

    ercot_snapshot = services.ercot_service.get_realtime_snapshot()
    map_events: list[MapEventState] = []
    for event in events:
        forecast = _ensure_forecast(event, services)
        weather = services.weather_service.get_weather_for_event(event)
        energy_profile = services.weather_service.get_event_energy_profile(
            event=event,
            temperature_override_f=weather.temperature_f,
        )
        zip_projections = services.demand_wave_service.project_wave(
            event=event,
            adjusted_attendance=forecast.adjusted_attendance,
            weather_multiplier=energy_profile.weather_multiplier,
            venue_intensity_factor=energy_profile.venue_intensity_factor,
        )
        heat_ratio = forecast.adjusted_attendance / max(event.baseline_attendance, 1)
        map_events.append(
            MapEventState(
                event_id=event.event_id,
                name=event.name,
                venue=event.venue,
                latitude=event.latitude,
                longitude=event.longitude,
                baseline_attendance=event.baseline_attendance,
                adjusted_attendance=forecast.adjusted_attendance,
                confidence=forecast.confidence,
                projected_dispersal_peak=event.projected_dispersal_peak,
                heat_intensity=min(max(heat_ratio, 0.1), 1.0),
                weather_multiplier=energy_profile.weather_multiplier,
                wave_zip_codes=[item.zip_code for item in zip_projections],
            )
        )

    return MapStateResponse(as_of=ercot_snapshot.updated_at, ercot=ercot_snapshot, events=map_events)


@router.post("/simulate", response_model=WeatherSimulationResponse)
def simulate_weather(payload: WeatherSimulationRequest, services=Depends(get_services)) -> WeatherSimulationResponse:
    event = services.event_ingestion.get_event(payload.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    forecast = _ensure_forecast(event, services)
    weather = services.weather_service.get_weather_for_event(event, temperature_override_f=payload.temperature_f)
    energy_profile = services.weather_service.get_event_energy_profile(
        event=event,
        temperature_override_f=weather.temperature_f,
    )
    zip_projections = services.demand_wave_service.project_wave(
        event=event,
        adjusted_attendance=forecast.adjusted_attendance,
        weather_multiplier=energy_profile.weather_multiplier,
        venue_intensity_factor=energy_profile.venue_intensity_factor,
    )

    return WeatherSimulationResponse(
        event_id=event.event_id,
        temperature_f=weather.temperature_f,
        weather_multiplier=energy_profile.weather_multiplier,
        energy_profile=energy_profile,
        projected_peak_mw=services.demand_wave_service.peak_mw(zip_projections),
        forecast=ForecastResponse.model_validate(forecast.model_dump()),
        zip_projections=zip_projections,
    )


@router.get("/urban-overlays", response_model=UrbanOverlaysResponse)
def get_urban_overlays(services=Depends(get_services)) -> UrbanOverlaysResponse:
    return UrbanOverlaysResponse(
        stations=services.urban_planning_service.get_project_connect_stations(),
        capital_projects=services.urban_planning_service.get_capital_projects(),
        zoning_corridors=services.urban_planning_service.get_zoning_corridors(),
    )


@router.post("/urban-simulate", response_model=UrbanSimulationResponse)
def simulate_urban_project(
    payload: UrbanSimulationRequest,
    services=Depends(get_services),
) -> UrbanSimulationResponse:
    simulation = services.urban_planning_service.simulate_project(
        project_id=payload.project_id,
        project_name=payload.project_name,
        horizon_years=payload.horizon_years,
        building_units=payload.building_units,
        commercial_sqft=payload.commercial_sqft,
    )
    return UrbanSimulationResponse(simulation=simulation)
