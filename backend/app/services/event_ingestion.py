from datetime import datetime, timezone
from typing import Protocol

from app.models.event import Event
from app.schemas.events import EventIngestItem
from app.services.dispersal_model import estimate_baseline_attendance, estimate_dispersal_window


class EventSourceAdapter(Protocol):
    source_name: str

    def fetch(self) -> list[EventIngestItem]:
        ...


def _slugify(value: str) -> str:
    return "-".join(value.strip().lower().split())


class EventIngestionService:
    def __init__(self, default_radius_meters: int) -> None:
        self.default_radius_meters = default_radius_meters
        self._events: dict[str, Event] = {}

    def ingest_events(self, raw_events: list[EventIngestItem]) -> list[Event]:
        ingested: list[Event] = []
        for raw_event in raw_events:
            event = self._to_canonical_event(raw_event)
            self._events[event.event_id] = event
            ingested.append(event)
        return ingested

    def ingest_from_adapter(self, adapter: EventSourceAdapter) -> list[Event]:
        events = adapter.fetch()
        return self.ingest_events(events)

    def list_events(self) -> list[Event]:
        return sorted(self._events.values(), key=lambda event: event.start_time)

    def get_event(self, event_id: str) -> Event | None:
        return self._events.get(event_id)

    def list_active_events(self, at: datetime | None = None) -> list[Event]:
        target_time = at or datetime.now(timezone.utc)
        active = [
            event
            for event in self._events.values()
            if event.start_time <= target_time <= event.projected_dispersal_end
        ]
        return sorted(active, key=lambda event: event.start_time)

    def _to_canonical_event(self, raw_event: EventIngestItem) -> Event:
        baseline_attendance = estimate_baseline_attendance(raw_event)
        dispersal_peak, dispersal_end = estimate_dispersal_window(
            event_end_time=raw_event.end_time,
            attendance=baseline_attendance,
            venue=raw_event.venue,
            parking_infrastructure_score=raw_event.parking_infrastructure_score,
            transit_access_score=raw_event.transit_access_score,
        )
        event_id = raw_event.source_event_id or (
            f"{raw_event.source}-{_slugify(raw_event.venue)}-{int(raw_event.start_time.timestamp())}"
        )
        return Event(
            event_id=event_id,
            name=raw_event.name,
            source=raw_event.source,
            venue=raw_event.venue,
            start_time=raw_event.start_time,
            end_time=raw_event.end_time,
            baseline_attendance=baseline_attendance,
            latitude=raw_event.latitude,
            longitude=raw_event.longitude,
            radius_meters=raw_event.radius_meters or self.default_radius_meters,
            projected_dispersal_peak=dispersal_peak,
            projected_dispersal_end=dispersal_end,
            parking_infrastructure_score=raw_event.parking_infrastructure_score,
            transit_access_score=raw_event.transit_access_score,
            ingested_at=datetime.now(timezone.utc),
        )


class UTAustinCalendarAdapter:
    source_name = "ut_calendar"

    def __init__(self, calendar_url: str | None) -> None:
        self.calendar_url = calendar_url

    def fetch(self) -> list[EventIngestItem]:
        # Adapter shape for a real source; MVP defaults to manual/mock ingestion.
        if not self.calendar_url:
            return []
        return []
