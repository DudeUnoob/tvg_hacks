from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class EventIngestItem(BaseModel):
    source_event_id: str | None = None
    name: str
    source: str = "manual"
    venue: str
    start_time: datetime
    end_time: datetime
    expected_attendance: int | None = Field(default=None, ge=0)
    expected_capacity: int | None = Field(default=None, ge=0)
    latitude: float
    longitude: float
    radius_meters: int | None = Field(default=None, ge=100)
    parking_infrastructure_score: float = Field(default=0.6, ge=0.0, le=1.0)
    transit_access_score: float = Field(default=0.5, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_times(self) -> "EventIngestItem":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class EventIngestRequest(BaseModel):
    events: list[EventIngestItem] = Field(min_length=1)


class EventResponse(BaseModel):
    event_id: str
    name: str
    source: str
    venue: str
    start_time: datetime
    end_time: datetime
    baseline_attendance: int
    latitude: float
    longitude: float
    radius_meters: int
    projected_dispersal_peak: datetime
    projected_dispersal_end: datetime
    parking_infrastructure_score: float
    transit_access_score: float


class EventListResponse(BaseModel):
    events: list[EventResponse]


class EventIngestResponse(BaseModel):
    ingested_count: int
    events: list[EventResponse]
