from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _ingest_single_event(client: TestClient) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "events": [
            {
                "source_event_id": "moody-test-event",
                "name": "Moody Test Event",
                "source": "ticketmaster",
                "venue": "Moody Center",
                "start_time": (now - timedelta(hours=1)).isoformat(),
                "end_time": (now + timedelta(minutes=30)).isoformat(),
                "expected_attendance": 14000,
                "latitude": 30.2804,
                "longitude": -97.7320,
                "parking_infrastructure_score": 0.68,
                "transit_access_score": 0.58,
            }
        ]
    }
    response = client.post("/events/ingest", json=payload)
    assert response.status_code == 200
    return response.json()["events"][0]["event_id"]


def test_layer2_confirmation_and_forecast_path() -> None:
    app = create_app(Settings(mock_mode=True, mock_empty_frames=False))
    client = TestClient(app)
    event_id = _ingest_single_event(client)

    crowd_response = client.post(f"/crowd/confirm/{event_id}", json={"sample_size": 4})
    assert crowd_response.status_code == 200
    crowd_body = crowd_response.json()
    assert crowd_body["camera_count"] == 4
    assert 0.0 <= crowd_body["confidence"] <= 1.0
    assert crowd_body["fallback_used"] is False

    forecast_response = client.get(f"/forecasts/{event_id}")
    assert forecast_response.status_code == 200
    forecast_body = forecast_response.json()
    assert forecast_body["vlm_estimated_attendance"] > 0
    assert forecast_body["adjusted_attendance"] > 0
    assert forecast_body["reasoning_trace"]


def test_layer2_fallback_when_frames_unavailable() -> None:
    app = create_app(Settings(mock_mode=True, mock_empty_frames=True))
    client = TestClient(app)
    event_id = _ingest_single_event(client)

    crowd_response = client.post(f"/crowd/confirm/{event_id}", json={"sample_size": 3})
    assert crowd_response.status_code == 200
    crowd_body = crowd_response.json()
    assert crowd_body["fallback_used"] is True

    forecast_response = client.get(f"/forecasts/{event_id}")
    assert forecast_response.status_code == 200
    forecast_body = forecast_response.json()
    assert forecast_body["fallback_used"] is True
    assert forecast_body["adjusted_attendance"] == forecast_body["baseline_attendance"]
