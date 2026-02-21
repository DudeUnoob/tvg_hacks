from datetime import datetime

from pydantic import BaseModel, Field


class Forecast(BaseModel):
    event_id: str
    generated_at: datetime
    baseline_attendance: int = Field(ge=0)
    vlm_estimated_attendance: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    adjusted_attendance: int = Field(ge=0)
    adjustment_delta: int
    fallback_used: bool = False
    reasoning_trace: str
