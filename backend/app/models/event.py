from datetime import datetime

from pydantic import BaseModel, Field


class Event(BaseModel):
    event_id: str
    name: str
    source: str
    venue: str
    start_time: datetime
    end_time: datetime
    baseline_attendance: int = Field(ge=0)
    latitude: float
    longitude: float
    radius_meters: int = Field(ge=100)
    projected_dispersal_peak: datetime
    projected_dispersal_end: datetime
    parking_infrastructure_score: float = Field(ge=0.0, le=1.0)
    transit_access_score: float = Field(ge=0.0, le=1.0)
    ingested_at: datetime
