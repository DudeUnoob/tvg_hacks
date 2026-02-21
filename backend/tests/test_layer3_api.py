from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _ingest_active_event(client: TestClient) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "events": [
            {
                "source_event_id": "layer3-live-event",
                "name": "Layer 3 Live Event",
                "source": "manual",
                "venue": "DKR-Texas Memorial Stadium",
                "start_time": (now - timedelta(minutes=20)).isoformat(),
                "end_time": (now + timedelta(minutes=65)).isoformat(),
                "expected_attendance": 92000,
                "latitude": 30.2839,
                "longitude": -97.7323,
                "parking_infrastructure_score": 0.74,
                "transit_access_score": 0.65,
            }
        ]
    }
    response = client.post("/events/ingest", json=payload)
    assert response.status_code == 200
    return response.json()["events"][0]["event_id"]


def test_layer3_map_state_and_weather_simulation() -> None:
    app = create_app(Settings(mock_mode=True, weather_source="mock", ercot_source="mock"))
    client = TestClient(app)
    event_id = _ingest_active_event(client)

    map_state_response = client.get("/layer3/map-state")
    assert map_state_response.status_code == 200
    map_state = map_state_response.json()
    assert map_state["ercot"]["price_mwh"] > 0
    assert len(map_state["events"]) > 0
    assert map_state["events"][0]["weather_multiplier"] > 0

    simulate_response = client.post(
        "/layer3/simulate",
        json={"event_id": event_id, "temperature_f": 101},
    )
    assert simulate_response.status_code == 200
    simulation = simulate_response.json()
    assert simulation["temperature_f"] == 101
    assert simulation["weather_multiplier"] > 0
    assert simulation["energy_profile"]["source"] in {"comprehensive_csv", "fallback_curve"}
    assert simulation["weather_multiplier"] == simulation["energy_profile"]["weather_multiplier"]
    assert len(simulation["zip_projections"]) > 0


def test_layer3_urban_overlays_and_simcity_simulation() -> None:
    app = create_app(Settings(mock_mode=True, weather_source="mock", ercot_source="mock"))
    client = TestClient(app)

    overlays_response = client.get("/layer3/urban-overlays")
    assert overlays_response.status_code == 200
    overlays = overlays_response.json()
    assert len(overlays["stations"]) > 0
    assert len(overlays["capital_projects"]) > 0
    assert len(overlays["zoning_corridors"]) > 0

    urban_sim_response = client.post(
        "/layer3/urban-simulate",
        json={
            "project_name": "SimCity Apartment Cluster",
            "horizon_years": 10,
            "building_units": 1000,
            "commercial_sqft": 260000,
        },
    )
    assert urban_sim_response.status_code == 200
    simulation = urban_sim_response.json()["simulation"]
    assert simulation["projected_load_mw"] > 0
    assert simulation["recommended_battery_count"] >= 0
