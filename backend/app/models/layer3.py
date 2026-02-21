from datetime import datetime

from pydantic import BaseModel, Field


class WeatherSnapshot(BaseModel):
    temperature_f: float
    humidity_pct: float = Field(ge=0.0, le=100.0)
    condition: str
    source: str
    observed_at: datetime


class ErcotSnapshot(BaseModel):
    price_mwh: float = Field(ge=0.0)
    load_mw: float = Field(ge=0.0)
    source: str
    updated_at: datetime


class ZipLoadProjection(BaseModel):
    zip_code: str
    projected_load_delta_mw: float = Field(ge=0.0)
    share_of_wave_pct: float = Field(ge=0.0, le=1.0)
    peak_time: datetime


class MapEventState(BaseModel):
    event_id: str
    name: str
    venue: str
    latitude: float
    longitude: float
    baseline_attendance: int = Field(ge=0)
    adjusted_attendance: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    projected_dispersal_peak: datetime
    heat_intensity: float = Field(ge=0.0, le=1.0)
    wave_zip_codes: list[str]


class UrbanStation(BaseModel):
    station_id: str
    name: str
    latitude: float
    longitude: float
    corridor: str


class CapitalProject(BaseModel):
    project_id: str
    name: str
    latitude: float
    longitude: float
    status: str
    estimated_budget_usd: float = Field(ge=0.0)


class ZoningCorridor(BaseModel):
    corridor_id: str
    name: str
    latitude: float
    longitude: float
    zoning_type: str
    density_multiplier: float = Field(ge=0.0)


class UrbanSimulationResult(BaseModel):
    scenario_id: str
    scenario_name: str
    horizon_years: int = Field(ge=1, le=30)
    projected_load_mw: float = Field(ge=0.0)
    current_capacity_mw: float = Field(ge=0.0)
    transformer_headroom_mw: float
    recommended_battery_count: int = Field(ge=0)
    grid_stress_level: str
