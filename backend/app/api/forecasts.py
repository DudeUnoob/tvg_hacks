from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_services
from app.schemas.forecast import ForecastResponse

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


@router.get("/{event_id}", response_model=ForecastResponse)
def get_event_forecast(
    event_id: str,
    refresh: bool = Query(default=False),
    services=Depends(get_services),
) -> ForecastResponse:
    event = services.event_ingestion.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    crowd_signal = services.latest_signals.get(event_id)
    if refresh or crowd_signal is None:
        frames = services.frame_provider.get_frames(event=event, sample_size=3)
        crowd_signal = services.vlm_estimator.estimate(event=event, frames=frames)
        services.latest_signals[event_id] = crowd_signal

    forecast = services.crowd_fusion.build_forecast(event=event, crowd_signal=crowd_signal)
    services.latest_forecasts[event_id] = forecast
    return ForecastResponse.model_validate(forecast.model_dump())
