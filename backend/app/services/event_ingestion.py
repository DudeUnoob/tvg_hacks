import csv
from datetime import datetime, time, timedelta, timezone
import json
from pathlib import Path
import re
from typing import Any, Protocol
from zoneinfo import ZoneInfo

import httpx

from app.models.event import Event
from app.schemas.events import EventIngestItem
from app.services.dispersal_model import estimate_baseline_attendance, estimate_dispersal_window


class EventSourceAdapter(Protocol):
    source_name: str

    def fetch(self) -> list[EventIngestItem]:
        ...


def _slugify(value: str) -> str:
    return "-".join(value.strip().lower().split())


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _resolve_austin_venue(venue_text: str | None) -> tuple[str, float, float, int]:
    venue = (venue_text or "").strip()
    normalized = venue.lower()
    if "darrell" in normalized or "dkr" in normalized or "memorial stadium" in normalized:
        return "DKR-Texas Memorial Stadium", 30.2839, -97.7323, 100_247
    if "moody" in normalized:
        return "Moody Center", 30.2804, -97.7320, 15_000
    if "cota" in normalized or "circuit of the americas" in normalized:
        return "Circuit of the Americas", 30.1328, -97.6411, 120_000
    if "acl" in normalized or "zilker" in normalized:
        return "Zilker Park", 30.2669, -97.7725, 75_000
    return venue or "Austin Venue", 30.2672, -97.7431, 20_000


def _safe_float(value: object, fallback: float) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return fallback


def _safe_int(value: object, fallback: int | None = None) -> int | None:
    try:
        if value is None:
            return fallback
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return fallback


class CsvSportsEventsAdapter:
    source_name = "ut_sports_csv"
    _austin_tz = ZoneInfo("America/Chicago")
    _default_duration_hours = 3
    _venue_coords: dict[str, tuple[float, float]] = {
        "dkr-texas memorial stadium": (30.2839, -97.7323),
        "moody center": (30.2804, -97.7320),
        "mike a. myers stadium and soccer field": (30.2865, -97.7321),
        "ufcu disch-falk field": (30.2806, -97.7314),
        "gregory gymnasium": (30.2845, -97.7384),
        "texas tennis center": (30.2682, -97.7273),
        "weller tennis center": (30.2734, -97.7201),
        "lee and joe jamail texas swimming center": (30.2836, -97.7334),
        "red & charline mccombs field": (30.2802, -97.7348),
        "wright-whitaker sports complex": (30.2769, -97.7139),
    }
    _category_duration_hours: dict[str, int] = {
        "football": 4,
        "baseball": 3,
        "softball": 3,
        "men's basketball": 3,
        "women's basketball": 3,
        "men's tennis": 3,
        "women's tennis": 3,
        "men's swimming and diving": 3,
        "women's swimming and diving": 3,
        "track & field / cross country": 8,
        "rowing": 6,
        "women's golf": 7,
        "beach volleyball": 3,
    }
    _category_capacity_hints: dict[str, int] = {
        "rowing": 3000,
        "women's golf": 2000,
        "track & field / cross country": 20000,
        "football": 100000,
        "baseball": 7373,
        "softball": 1252,
        "beach volleyball": 640,
    }
    _category_start_hour_hints: dict[str, int] = {
        "football": 18,
        "baseball": 18,
        "softball": 18,
        "men's basketball": 19,
        "women's basketball": 19,
        "rowing": 9,
        "women's golf": 10,
        "track & field / cross country": 10,
    }

    def __init__(
        self,
        events_csv_path: str,
        venues_capacity_csv_path: str | None = None,
        facility_energy_csv_path: str | None = None,
    ) -> None:
        self.events_csv_path = events_csv_path
        self.venues_capacity_csv_path = venues_capacity_csv_path
        self.facility_energy_csv_path = facility_energy_csv_path

    def fetch(self) -> list[EventIngestItem]:
        events_path = self._resolve_path(self.events_csv_path)
        if events_path is None or not events_path.exists():
            return []

        capacities = self._load_capacity_map()
        energy_index = self._load_energy_map()
        now = datetime.now(timezone.utc)
        items: list[EventIngestItem] = []

        with events_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for index, row in enumerate(reader, start=1):
                event_name = str(row.get("Event") or "").strip()
                category = str(row.get("Category") or "").strip()
                if not event_name:
                    continue

                start = self._parse_local_datetime(
                    date_text=str(row.get("Start Date") or ""),
                    time_text=str(row.get("Start Time") or ""),
                    default_hour=self._category_start_hour_hints.get(category.lower(), 18),
                )
                if start is None:
                    continue

                end = self._parse_local_datetime(
                    date_text=str(row.get("End Date") or row.get("Start Date") or ""),
                    time_text=str(row.get("End Time") or ""),
                    default_hour=(start.astimezone(self._austin_tz).hour + self._duration_hours(category)),
                )
                if end is None:
                    end = start + timedelta(hours=self._duration_hours(category))

                if end <= start:
                    end = end + timedelta(days=1)
                if (end - start) > timedelta(hours=12):
                    end = start + timedelta(hours=self._duration_hours(category))
                if end <= now - timedelta(hours=8):
                    continue

                facility_name = str(row.get("Facility") or "").strip()
                if not facility_name:
                    facility_name = self._derive_facility_name(category)

                normalized_facility = facility_name.lower()
                venue, fallback_lat, fallback_lon, fallback_capacity = _resolve_austin_venue(facility_name)
                latitude, longitude = self._venue_coords.get(normalized_facility, (fallback_lat, fallback_lon))

                expected_capacity = capacities.get(normalized_facility) or self._category_capacity_hints.get(
                    category.lower(), fallback_capacity
                )
                energy_usage = energy_index.get(normalized_facility)

                items.append(
                    EventIngestItem(
                        source_event_id=self._event_id(event_name, venue, start, index),
                        name=event_name,
                        source=self.source_name,
                        venue=venue,
                        start_time=start,
                        end_time=end,
                        expected_capacity=expected_capacity,
                        latitude=latitude,
                        longitude=longitude,
                        radius_meters=self._radius_for(expected_capacity, energy_usage),
                        parking_infrastructure_score=self._parking_score(venue, expected_capacity, energy_usage),
                        transit_access_score=self._transit_score(venue, expected_capacity),
                    )
                )
        return items

    @staticmethod
    def _resolve_path(path_value: str | None) -> Path | None:
        if not path_value:
            return None
        candidate = Path(path_value).expanduser()
        if candidate.exists():
            return candidate
        backend_root = Path(__file__).resolve().parents[2]
        backend_candidate = backend_root / candidate
        if backend_candidate.exists():
            return backend_candidate
        repo_candidate = backend_root.parent / candidate
        if repo_candidate.exists():
            return repo_candidate
        return candidate

    def _load_capacity_map(self) -> dict[str, int]:
        path = self._resolve_path(self.venues_capacity_csv_path)
        if path is None or not path.exists():
            return {}
        capacities: dict[str, int] = {}
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                venue = str(row.get("Venue") or "").strip().lower()
                capacity = _safe_int(row.get("Capacity"))
                if venue and capacity:
                    capacities[venue] = capacity
        return capacities

    def _load_energy_map(self) -> dict[str, int]:
        path = self._resolve_path(self.facility_energy_csv_path)
        if path is None or not path.exists():
            return {}
        energy: dict[str, int] = {}
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                venue = str(row.get("Center Name") or "").strip().lower()
                usage = _safe_int(row.get("Energy Usage"))
                if venue and usage:
                    energy[venue] = usage
        return energy

    def _parse_local_datetime(self, date_text: str, time_text: str, default_hour: int) -> datetime | None:
        try:
            event_date = datetime.strptime(date_text.strip(), "%m/%d/%Y").date()
        except ValueError:
            return None

        parsed_time = self._parse_time_token(time_text)
        if parsed_time is None:
            parsed_time = time(hour=max(0, min(default_hour, 23)), minute=0)

        local_dt = datetime.combine(event_date, parsed_time).replace(tzinfo=self._austin_tz)
        return local_dt.astimezone(timezone.utc)

    @staticmethod
    def _parse_time_token(raw_value: str) -> time | None:
        text = raw_value.strip()
        if not text:
            return None
        upper = text.upper()
        if "TBA" in upper:
            return None

        cleaned = upper.replace("A.M.", "AM").replace("P.M.", "PM")
        cleaned = cleaned.replace("A.M", "AM").replace("P.M", "PM")
        cleaned = cleaned.replace("AM.", "AM").replace("PM.", "PM")
        cleaned = re.sub(r"\bCT\b", "", cleaned)
        cleaned = re.sub(r"[^0-9APM: ]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            return None

        for fmt in ("%I:%M%p", "%I:%M %p", "%I%p", "%I %p", "%H:%M"):
            try:
                return datetime.strptime(cleaned, fmt).time()
            except ValueError:
                continue
        return None

    def _duration_hours(self, category: str) -> int:
        return self._category_duration_hours.get(category.lower(), self._default_duration_hours)

    @staticmethod
    def _derive_facility_name(category: str) -> str:
        normalized = category.strip().lower()
        if "rowing" in normalized:
            return "Lady Bird Lake"
        if "golf" in normalized:
            return "UT Golf Club"
        return "Austin Venue"

    @staticmethod
    def _event_id(event_name: str, venue: str, start_time: datetime, index: int) -> str:
        return (
            f"utcsv-{start_time.strftime('%Y%m%d%H%M')}-{index}-"
            f"{_slugify(event_name)[:48]}-{_slugify(venue)[:24]}"
        )

    @staticmethod
    def _radius_for(capacity: int, energy_usage: int | None) -> int:
        cap = max(capacity, 0)
        radius = 1200 + int((min(cap, 110_000) / 110_000) * 2000)
        if energy_usage is not None:
            radius += min(500, energy_usage * 40)
        return max(900, min(radius, 4200))

    @staticmethod
    def _parking_score(venue: str, capacity: int, energy_usage: int | None) -> float:
        normalized = venue.lower()
        if "stadium" in normalized:
            return 0.74
        if "moody" in normalized:
            return 0.68
        cap_component = min(capacity, 40_000) / 40_000
        energy_component = min(energy_usage or 0, 12) / 12
        return round(min(0.82, 0.56 + (cap_component * 0.14) + (energy_component * 0.07)), 3)

    @staticmethod
    def _transit_score(venue: str, capacity: int) -> float:
        normalized = venue.lower()
        if "stadium" in normalized or "moody" in normalized or "gregory" in normalized:
            return 0.63
        if capacity >= 10_000:
            return 0.58
        return 0.5


class LocalistEventsAdapter:
    def __init__(
        self,
        api_url: str,
        source_name: str,
        search_term: str,
        results_per_page: int,
        keyword_filters: list[str] | None = None,
    ) -> None:
        self.api_url = api_url
        self.source_name = source_name
        self.search_term = search_term
        self.results_per_page = results_per_page
        self.keyword_filters = [item.lower() for item in (keyword_filters or [])]

    def fetch(self) -> list[EventIngestItem]:
        params = {
            "pp": str(self.results_per_page),
            "days": "120",
            "search": self.search_term,
        }
        with httpx.Client(timeout=10.0) as client:
            response = client.get(self.api_url, params=params)
            response.raise_for_status()
            body = response.json()

        rows = body.get("events", [])
        now = datetime.now(timezone.utc)
        items: list[EventIngestItem] = []
        for wrapper in rows:
            event = wrapper.get("event", {})
            event_id = event.get("id")
            if not event_id:
                continue

            instance = ((event.get("event_instances") or [{}])[0]).get("event_instance", {})
            start = _parse_datetime(instance.get("start")) or _parse_datetime(event.get("first_date"))
            if start is None:
                continue

            end = _parse_datetime(instance.get("end"))
            if end is None:
                end = start + timedelta(hours=3)
            if end <= now - timedelta(hours=8):
                continue

            title = str(event.get("title") or "UT Austin event").replace("\xa0", " ").strip()
            location_name = event.get("location_name") or event.get("location")
            searchable = f"{title} {location_name or ''}".lower()
            if self.keyword_filters and not any(keyword in searchable for keyword in self.keyword_filters):
                continue
            venue, fallback_lat, fallback_lon, expected_capacity = _resolve_austin_venue(location_name)
            geo = event.get("geo") or {}
            latitude = _safe_float(geo.get("latitude"), fallback_lat)
            longitude = _safe_float(geo.get("longitude"), fallback_lon)

            items.append(
                EventIngestItem(
                    source_event_id=f"{self.source_name}-{event_id}",
                    name=title,
                    source=self.source_name,
                    venue=venue,
                    start_time=start,
                    end_time=end,
                    expected_capacity=expected_capacity,
                    latitude=latitude,
                    longitude=longitude,
                    radius_meters=2800 if "stadium" in venue.lower() else 2000,
                    parking_infrastructure_score=0.72 if "stadium" in venue.lower() else 0.66,
                    transit_access_score=0.63,
                )
            )
        return items


class MoodyCenterWebAdapter:
    source_name = "moody_web"

    def __init__(self, events_url: str) -> None:
        self.events_url = events_url

    def fetch(self) -> list[EventIngestItem]:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(self.events_url)
            response.raise_for_status()
            html = response.text

        scripts = re.findall(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            html,
            re.S,
        )
        if not scripts:
            return []

        payload: list[dict[str, Any]] = []
        for block in scripts:
            try:
                parsed = json.loads(block)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, list):
                payload.extend([item for item in parsed if isinstance(item, dict)])

        items: list[EventIngestItem] = []
        now = datetime.now(timezone.utc)
        for index, event in enumerate(payload):
            if event.get("@type") != "Event":
                continue
            start = _parse_datetime(event.get("startDate"))
            if start is None:
                continue
            end = _parse_datetime(event.get("endDate")) or (start + timedelta(hours=3))
            if end <= now - timedelta(hours=8):
                continue

            name = str(event.get("name") or "Moody Center event").strip()
            source_event_id = (
                str(event.get("url") or f"moody-{start.isoformat()}-{index}")
                .replace("https://", "")
                .replace("/", "-")
            )
            items.append(
                EventIngestItem(
                    source_event_id=source_event_id,
                    name=name,
                    source=self.source_name,
                    venue="Moody Center",
                    start_time=start,
                    end_time=end,
                    expected_capacity=15_000,
                    latitude=30.2804,
                    longitude=-97.7320,
                    radius_meters=2000,
                    parking_infrastructure_score=0.68,
                    transit_access_score=0.59,
                )
            )
        return items


class TicketmasterDiscoveryAdapter:
    source_name = "ticketmaster"

    def __init__(self, api_url: str, api_key: str) -> None:
        self.api_url = api_url
        self.api_key = api_key

    def fetch(self) -> list[EventIngestItem]:
        params = {
            "apikey": self.api_key,
            "city": "Austin",
            "stateCode": "TX",
            "countryCode": "US",
            "classificationName": "music,sports",
            "size": "50",
            "sort": "date,asc",
        }
        with httpx.Client(timeout=12.0) as client:
            response = client.get(self.api_url, params=params)
            response.raise_for_status()
            body = response.json()

        rows = (body.get("_embedded") or {}).get("events", [])
        items: list[EventIngestItem] = []
        now = datetime.now(timezone.utc)
        for event in rows:
            start = _parse_datetime(((event.get("dates") or {}).get("start") or {}).get("dateTime"))
            if start is None:
                continue
            end = start + timedelta(hours=3)
            if end <= now - timedelta(hours=8):
                continue

            venues = ((event.get("_embedded") or {}).get("venues") or [{}])
            venue_obj = venues[0]
            venue_name = venue_obj.get("name")
            venue, fallback_lat, fallback_lon, expected_capacity = _resolve_austin_venue(venue_name)
            location = venue_obj.get("location") or {}
            latitude = _safe_float(location.get("latitude"), fallback_lat)
            longitude = _safe_float(location.get("longitude"), fallback_lon)

            event_name = str(event.get("name") or "Austin Ticketmaster event").strip()
            event_id = str(event.get("id") or f"tm-{int(start.timestamp())}")
            items.append(
                EventIngestItem(
                    source_event_id=f"tm-{event_id}",
                    name=event_name,
                    source=self.source_name,
                    venue=venue,
                    start_time=start,
                    end_time=end,
                    expected_capacity=expected_capacity,
                    latitude=latitude,
                    longitude=longitude,
                    radius_meters=2500,
                    parking_infrastructure_score=0.66,
                    transit_access_score=0.58,
                )
            )
        return items


class EventIngestionService:
    def __init__(
        self,
        default_radius_meters: int,
        live_sync_interval_seconds: int = 300,
        live_adapters: list[EventSourceAdapter] | None = None,
    ) -> None:
        self.default_radius_meters = default_radius_meters
        self.live_sync_interval_seconds = live_sync_interval_seconds
        self._last_live_sync_at: datetime | None = None
        self._live_adapters: list[EventSourceAdapter] = live_adapters or []
        self._events: dict[str, Event] = {}

    def ingest_events(self, raw_events: list[EventIngestItem]) -> list[Event]:
        ingested: list[Event] = []
        for raw_event in raw_events:
            event = self._to_canonical_event(raw_event)
            self._events[event.event_id] = event
            ingested.append(event)
        return ingested

    def ingest_from_adapter(self, adapter: EventSourceAdapter) -> list[Event]:
        events = adapter.fetch()
        return self.ingest_events(events)

    def list_events(self) -> list[Event]:
        return sorted(self._events.values(), key=lambda event: event.start_time)

    def get_event(self, event_id: str) -> Event | None:
        return self._events.get(event_id)

    def register_live_adapters(self, adapters: list[EventSourceAdapter]) -> None:
        self._live_adapters = adapters

    def list_active_events(self, at: datetime | None = None) -> list[Event]:
        target_time = at or datetime.now(timezone.utc)
        active = [
            event
            for event in self._events.values()
            if event.start_time <= target_time <= event.projected_dispersal_end
        ]
        return sorted(active, key=lambda event: event.start_time)

    def sync_live_events(self, force: bool = False) -> list[Event]:
        now = datetime.now(timezone.utc)
        if not self._live_adapters:
            return []
        if (
            not force
            and self._last_live_sync_at is not None
            and (now - self._last_live_sync_at).total_seconds() < self.live_sync_interval_seconds
        ):
            return []

        staged_by_id: dict[str, EventIngestItem] = {}
        for adapter in self._live_adapters:
            try:
                events = adapter.fetch()
            except Exception:
                continue
            for event in events:
                key = event.source_event_id or (
                    f"{event.source}-{_slugify(event.venue)}-{int(event.start_time.timestamp())}"
                )
                staged_by_id[key] = event

        self._last_live_sync_at = now
        if not staged_by_id:
            return []
        return self.ingest_events(list(staged_by_id.values()))

    def _to_canonical_event(self, raw_event: EventIngestItem) -> Event:
        baseline_attendance = estimate_baseline_attendance(raw_event)
        dispersal_peak, dispersal_end = estimate_dispersal_window(
            event_end_time=raw_event.end_time,
            attendance=baseline_attendance,
            venue=raw_event.venue,
            parking_infrastructure_score=raw_event.parking_infrastructure_score,
            transit_access_score=raw_event.transit_access_score,
        )
        event_id = raw_event.source_event_id or (
            f"{raw_event.source}-{_slugify(raw_event.venue)}-{int(raw_event.start_time.timestamp())}"
        )
        return Event(
            event_id=event_id,
            name=raw_event.name,
            source=raw_event.source,
            venue=raw_event.venue,
            start_time=raw_event.start_time,
            end_time=raw_event.end_time,
            baseline_attendance=baseline_attendance,
            latitude=raw_event.latitude,
            longitude=raw_event.longitude,
            radius_meters=raw_event.radius_meters or self.default_radius_meters,
            projected_dispersal_peak=dispersal_peak,
            projected_dispersal_end=dispersal_end,
            parking_infrastructure_score=raw_event.parking_infrastructure_score,
            transit_access_score=raw_event.transit_access_score,
            ingested_at=datetime.now(timezone.utc),
        )


class UTAustinCalendarAdapter:
    source_name = "ut_calendar"

    def __init__(self, calendar_url: str | None) -> None:
        self.calendar_url = calendar_url

    def fetch(self) -> list[EventIngestItem]:
        # Adapter shape for a real source; MVP defaults to manual/mock ingestion.
        if not self.calendar_url:
            return []
        return []
