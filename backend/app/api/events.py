from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.deps import get_services
from app.models.event import Event
from app.schemas.events import (
    EventIngestRequest,
    EventIngestResponse,
    EventListResponse,
    EventResponse,
)

router = APIRouter(prefix="/events", tags=["events"])


class EventSyncResponse(BaseModel):
    ingested_count: int
    events: list[EventResponse]
    force: bool


def _to_event_response(event: Event) -> EventResponse:
    payload = event.model_dump(exclude={"ingested_at"})
    return EventResponse.model_validate(payload)


@router.post("/ingest", response_model=EventIngestResponse)
def ingest_events(payload: EventIngestRequest, services=Depends(get_services)) -> EventIngestResponse:
    ingested = services.event_ingestion.ingest_events(payload.events)
    return EventIngestResponse(
        ingested_count=len(ingested),
        events=[_to_event_response(event) for event in ingested],
    )


@router.post("/sync-live", response_model=EventSyncResponse)
def sync_live_events(
    force: bool = Query(default=False),
    services=Depends(get_services),
) -> EventSyncResponse:
    ingested = services.event_ingestion.sync_live_events(force=force)
    return EventSyncResponse(
        ingested_count=len(ingested),
        events=[_to_event_response(event) for event in ingested],
        force=force,
    )


@router.get("", response_model=EventListResponse)
def list_events(services=Depends(get_services)) -> EventListResponse:
    events = services.event_ingestion.list_events()
    return EventListResponse(events=[_to_event_response(event) for event in events])


@router.get("/active", response_model=EventListResponse)
def list_active_events(
    at: datetime | None = None,
    services=Depends(get_services),
) -> EventListResponse:
    active_events = services.event_ingestion.list_active_events(at=at)
    return EventListResponse(events=[_to_event_response(event) for event in active_events])
