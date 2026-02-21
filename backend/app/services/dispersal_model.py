from dataclasses import dataclass
from datetime import datetime, timedelta

from app.schemas.events import EventIngestItem


@dataclass(frozen=True)
class VenueProfile:
    capacity: int
    exit_rate_per_min: float
    default_occupancy: float


VENUE_PROFILES: dict[str, VenueProfile] = {
    "dkr": VenueProfile(capacity=100_247, exit_rate_per_min=1_400.0, default_occupancy=0.92),
    "moody center": VenueProfile(capacity=15_000, exit_rate_per_min=500.0, default_occupancy=0.88),
    "cota": VenueProfile(capacity=120_000, exit_rate_per_min=1_600.0, default_occupancy=0.84),
    "acl": VenueProfile(capacity=75_000, exit_rate_per_min=1_250.0, default_occupancy=0.90),
    "sxsw": VenueProfile(capacity=30_000, exit_rate_per_min=650.0, default_occupancy=0.82),
}

DEFAULT_PROFILE = VenueProfile(capacity=20_000, exit_rate_per_min=550.0, default_occupancy=0.8)


def _resolve_profile(venue: str) -> VenueProfile:
    normalized = venue.strip().lower()
    for key, profile in VENUE_PROFILES.items():
        if key in normalized:
            return profile
    return DEFAULT_PROFILE


def estimate_baseline_attendance(event: EventIngestItem) -> int:
    profile = _resolve_profile(event.venue)
    if event.expected_attendance is not None:
        return event.expected_attendance
    if event.expected_capacity is not None:
        return int(event.expected_capacity * 0.86)
    return int(profile.capacity * profile.default_occupancy)


def estimate_dispersal_window(
    event_end_time: datetime,
    attendance: int,
    venue: str,
    parking_infrastructure_score: float,
    transit_access_score: float,
) -> tuple[datetime, datetime]:
    profile = _resolve_profile(venue)
    base_minutes = max(20.0, attendance / max(profile.exit_rate_per_min, 1.0))

    # Lower parking/transit quality creates longer tail dispersal after event end.
    infrastructure_modifier = 1.2 - (parking_infrastructure_score * 0.18) - (transit_access_score * 0.12)
    total_minutes = int(min(max(base_minutes * infrastructure_modifier, 25.0), 180.0))

    peak = event_end_time + timedelta(minutes=int(total_minutes * 0.45))
    end = event_end_time + timedelta(minutes=total_minutes)
    return peak, end
