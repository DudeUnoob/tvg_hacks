from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _ingest_dispatch_event(client: TestClient) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "events": [
            {
                "source_event_id": "layer4-dispatch-event",
                "name": "Layer 4 Dispatch Event",
                "source": "manual",
                "venue": "Moody Center",
                "start_time": (now - timedelta(minutes=15)).isoformat(),
                "end_time": (now + timedelta(minutes=80)).isoformat(),
                "expected_attendance": 15500,
                "latitude": 30.2804,
                "longitude": -97.732,
                "parking_infrastructure_score": 0.66,
                "transit_access_score": 0.57,
            }
        ]
    }
    response = client.post("/events/ingest", json=payload)
    assert response.status_code == 200
    return response.json()["events"][0]["event_id"]


def test_layer4_dispatch_endpoints_return_ranked_targets() -> None:
    app = create_app(Settings(mock_mode=True))
    client = TestClient(app)
    event_id = _ingest_dispatch_event(client)

    active_response = client.get("/layer4/dispatch/active")
    assert active_response.status_code == 200
    active_recommendations = active_response.json()["recommendations"]
    assert len(active_recommendations) > 0
    assert len(active_recommendations[0]["targets"]) > 0

    event_response = client.get(f"/layer4/dispatch/{event_id}")
    assert event_response.status_code == 200
    recommendation = event_response.json()["recommendation"]
    assert recommendation["event_id"] == event_id
    assert recommendation["revenue_estimate_usd"] >= 0
    assert recommendation["lead_time_hours"] == 2
    assert "Layer 4 Dispatch Event" in recommendation["reasoning_trace"]


def test_layer4_dispatch_graceful_when_camera_frames_unavailable() -> None:
    app = create_app(Settings(mock_mode=True, mock_empty_frames=True))
    client = TestClient(app)
    event_id = _ingest_dispatch_event(client)

    response = client.get(f"/layer4/dispatch/{event_id}")
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert recommendation["event_id"] == event_id
    assert len(recommendation["targets"]) > 0
