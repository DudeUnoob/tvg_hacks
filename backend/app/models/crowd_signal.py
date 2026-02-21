from datetime import datetime

from pydantic import BaseModel, Field


class CrowdSignal(BaseModel):
    event_id: str
    observed_at: datetime
    camera_count: int = Field(ge=0)
    avg_parking_fill_pct: float = Field(ge=0.0, le=1.0)
    estimated_attendance: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    fallback_used: bool = False
    reasoning: str
