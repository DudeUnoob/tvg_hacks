from datetime import datetime

from pydantic import BaseModel, Field


class CrowdConfirmRequest(BaseModel):
    camera_ids: list[str] | None = None
    sample_size: int = Field(default=3, ge=1, le=10)


class CrowdSignalResponse(BaseModel):
    event_id: str
    observed_at: datetime
    camera_count: int
    avg_parking_fill_pct: float
    estimated_attendance: int
    confidence: float
    fallback_used: bool
    reasoning: str


class ForecastResponse(BaseModel):
    event_id: str
    generated_at: datetime
    baseline_attendance: int
    vlm_estimated_attendance: int
    confidence: float
    adjusted_attendance: int
    adjustment_delta: int
    fallback_used: bool
    reasoning_trace: str
