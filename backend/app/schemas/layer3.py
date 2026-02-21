from datetime import datetime

from pydantic import BaseModel, Field

from app.models.energy import VenueEnergyProfile
from app.models.layer3 import (
    CapitalProject,
    ErcotSnapshot,
    MapEventState,
    UrbanSimulationResult,
    UrbanStation,
    ZipLoadProjection,
    ZoningCorridor,
)
from app.schemas.forecast import ForecastResponse


class MapStateResponse(BaseModel):
    as_of: datetime
    ercot: ErcotSnapshot
    events: list[MapEventState]


class WeatherSimulationRequest(BaseModel):
    event_id: str
    temperature_f: float = Field(ge=20.0, le=115.0)


class WeatherSimulationResponse(BaseModel):
    event_id: str
    temperature_f: float
    weather_multiplier: float
    energy_profile: VenueEnergyProfile
    projected_peak_mw: float
    forecast: ForecastResponse
    zip_projections: list[ZipLoadProjection]


class UrbanOverlaysResponse(BaseModel):
    stations: list[UrbanStation]
    capital_projects: list[CapitalProject]
    zoning_corridors: list[ZoningCorridor]


class UrbanSimulationRequest(BaseModel):
    project_id: str | None = None
    project_name: str | None = None
    horizon_years: int = Field(default=5, ge=5, le=10)
    building_units: int | None = Field(default=None, ge=1)
    commercial_sqft: int | None = Field(default=None, ge=5000)


class UrbanSimulationResponse(BaseModel):
    simulation: UrbanSimulationResult
