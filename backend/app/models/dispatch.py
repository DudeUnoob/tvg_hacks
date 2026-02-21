from datetime import datetime

from pydantic import BaseModel, Field


class DispatchTarget(BaseModel):
    rank: int = Field(ge=1)
    zip_code: str
    recommended_capacity_pct: float = Field(ge=0.0, le=1.0)
    projected_load_delta_mw: float = Field(ge=0.0)
    estimated_battery_count: int = Field(ge=0)


class DispatchRecommendation(BaseModel):
    event_id: str
    event_name: str
    generated_at: datetime
    precharge_start_time: datetime
    lead_time_hours: int = Field(ge=1)
    confidence: float = Field(ge=0.0, le=1.0)
    temperature_f: float
    revenue_estimate_usd: float = Field(ge=0.0)
    comparable_signal: str
    reasoning_trace: str
    targets: list[DispatchTarget]
