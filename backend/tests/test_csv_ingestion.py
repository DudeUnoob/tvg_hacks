from datetime import datetime

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_sync_live_ingests_ut_csv_events_when_external_feeds_fail() -> None:
    app = create_app(
        Settings(
            mock_mode=True,
            auto_sync_live_events=False,
            weather_source="mock",
            ercot_source="mock",
            csv_events_enabled=True,
            ut_sports_csv_path="data/UT_Sports_Events.csv",
            venues_capacity_csv_path="data/venues_capacity.csv",
            facility_energy_csv_path="data/Facility_Energy_Usage.csv",
            ut_localist_api_url="http://127.0.0.1:9/events",
            moody_events_url="http://127.0.0.1:9/events",
        )
    )
    client = TestClient(app)

    response = client.post("/events/sync-live?force=true")
    assert response.status_code == 200

    body = response.json()
    assert body["ingested_count"] >= 20
    assert any(event["source"] == "ut_sports_csv" for event in body["events"])

    dkr_events = [event for event in body["events"] if event["venue"] == "DKR-Texas Memorial Stadium"]
    assert dkr_events
    assert max(event["baseline_attendance"] for event in dkr_events) >= 80_000

    for event in body["events"]:
        start = datetime.fromisoformat(event["start_time"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(event["end_time"].replace("Z", "+00:00"))
        assert end > start

    myers_event = next(
        (
            event
            for event in body["events"]
            if event["venue"] == "Mike A. Myers Stadium and Soccer Field"
        ),
        None,
    )
    assert myers_event is not None

    simulation_response = client.post(
        "/layer3/simulate",
        json={"event_id": myers_event["event_id"], "temperature_f": 85},
    )
    assert simulation_response.status_code == 200
    energy_profile = simulation_response.json()["energy_profile"]
    assert energy_profile["source"] == "comprehensive_csv"
    assert energy_profile["matched_venue"] == "Mike A. Myers Stadium"
