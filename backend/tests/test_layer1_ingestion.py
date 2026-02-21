import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _load_fixture_payload() -> dict:
    fixture_path = Path(__file__).parent / "fixtures" / "sample_events.json"
    return json.loads(fixture_path.read_text())


def test_layer1_ingest_populates_canonical_fields() -> None:
    app = create_app(Settings(mock_mode=True))
    client = TestClient(app)

    response = client.post("/events/ingest", json=_load_fixture_payload())
    assert response.status_code == 200

    body = response.json()
    assert body["ingested_count"] == 2

    first_event = body["events"][0]
    assert first_event["baseline_attendance"] > 0
    assert first_event["radius_meters"] >= 100
    assert first_event["projected_dispersal_peak"]
    assert first_event["projected_dispersal_end"]


def test_layer1_active_events_endpoint_returns_current_event() -> None:
    app = create_app(Settings(mock_mode=True))
    client = TestClient(app)

    now = datetime.now(timezone.utc)
    payload = {
        "events": [
            {
                "name": "Live Test Event",
                "source": "manual",
                "venue": "DKR-Texas Memorial Stadium",
                "start_time": (now - timedelta(minutes=45)).isoformat(),
                "end_time": (now + timedelta(minutes=15)).isoformat(),
                "expected_attendance": 80000,
                "latitude": 30.2839,
                "longitude": -97.7323,
                "parking_infrastructure_score": 0.7,
                "transit_access_score": 0.6,
            }
        ]
    }
    ingest_response = client.post("/events/ingest", json=payload)
    assert ingest_response.status_code == 200
    event_id = ingest_response.json()["events"][0]["event_id"]

    active_response = client.get("/events/active")
    assert active_response.status_code == 200
    active_ids = [event["event_id"] for event in active_response.json()["events"]]
    assert event_id in active_ids
