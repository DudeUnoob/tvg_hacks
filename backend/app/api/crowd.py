from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_services
from app.schemas.forecast import CrowdConfirmRequest, CrowdSignalResponse

router = APIRouter(prefix="/crowd", tags=["crowd"])


@router.post("/confirm/{event_id}", response_model=CrowdSignalResponse)
def confirm_crowd(
    event_id: str,
    payload: CrowdConfirmRequest,
    services=Depends(get_services),
) -> CrowdSignalResponse:
    event = services.event_ingestion.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    frames = services.frame_provider.get_frames(
        event=event,
        sample_size=payload.sample_size,
        camera_ids=payload.camera_ids,
    )
    crowd_signal = services.vlm_estimator.estimate(event=event, frames=frames)
    services.latest_signals[event_id] = crowd_signal
    return CrowdSignalResponse.model_validate(crowd_signal.model_dump())
