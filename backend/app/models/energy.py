from pydantic import BaseModel, Field


class VenueEnergyProfile(BaseModel):
    requested_venue: str
    matched_venue: str | None = None
    source: str
    temperature_f: float
    lower_bin_f: int | None = None
    upper_bin_f: int | None = None
    interpolated_kwh: float | None = Field(default=None, ge=0.0)
    base_kwh: float | None = Field(default=None, ge=0.0)
    weather_multiplier: float = Field(ge=0.0)
    venue_intensity_factor: float = Field(ge=0.0)
