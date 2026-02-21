# GridPulse Backend (Layer 1 to Layer 4 MVP)

This service now covers the core backend flow from `app_context/tvg.md`:

- Layer 1: Event ingestion + baseline attendance/dispersal modeling
- Layer 2: VLM-style crowd confirmation with confidence and fallback logic
- Layer 3: Real-time map state, weather simulation, and urban planning overlays/simulation
- Layer 4: Dispatch recommendation generation with ranked zip-code targeting

## Quick start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

API docs: `http://127.0.0.1:8000/docs`

## Core endpoints (Layer 1 + 2)

- `POST /events/ingest`: ingest raw events and normalize to canonical fields
- `GET /events`: list all ingested events
- `GET /events/active`: list currently active events
- `POST /crowd/confirm/{event_id}`: run crowd confirmation using frame provider + VLM adapter
- `GET /forecasts/{event_id}`: return fused baseline + VLM forecast

## Layer 3 endpoints

- `GET /layer3/map-state`: active event map state + ERCOT ticker snapshot
- `POST /layer3/simulate`: weather pressure test for an event (`event_id`, `temperature_f`) with energy profile output
- `GET /layer3/urban-overlays`: Project Connect stations, capital projects, zoning corridors
- `POST /layer3/urban-simulate`: 5/10-year urban impact simulation
- `POST /events/sync-live`: pull current events from live sources (local CSV, UT Localist, Moody page, optional Ticketmaster)

## Layer 4 endpoints

- `GET /layer4/dispatch/active`: ranked dispatch recommendations for active events (includes energy profile)
- `GET /layer4/dispatch/{event_id}`: dispatch recommendation for a specific event (includes energy profile)

## Demo flow

1. Ingest sample events:

```bash
curl -X POST "http://127.0.0.1:8000/events/ingest" \
  -H "Content-Type: application/json" \
  --data @tests/fixtures/sample_events.json
```

2. Confirm crowd for one event:

```bash
curl -X POST "http://127.0.0.1:8000/crowd/confirm/ut-vs-georgia-2026" \
  -H "Content-Type: application/json" \
  -d '{"sample_size": 4}'
```

3. Pull fused forecast:

```bash
curl "http://127.0.0.1:8000/forecasts/ut-vs-georgia-2026"
```

4. Pull Layer 3 map state:

```bash
curl "http://127.0.0.1:8000/layer3/map-state"
```

5. Run a weather pressure test:

```bash
curl -X POST "http://127.0.0.1:8000/layer3/simulate" \
  -H "Content-Type: application/json" \
  -d '{"event_id":"ut-vs-georgia-2026","temperature_f":102}'
```

6. Pull Layer 4 dispatch output:

```bash
curl "http://127.0.0.1:8000/layer4/dispatch/active"
```

7. Trigger live ingestion directly:

```bash
curl -X POST "http://127.0.0.1:8000/events/sync-live?force=true"
```

## Configuration

Environment variables are prefixed with `GRIDPULSE_`:

- `GRIDPULSE_MOCK_MODE=true`: use deterministic mock VLM estimates
- `GRIDPULSE_GEMINI_API_KEY`: enable real Gemini API calls when mock mode is `false`
- `GRIDPULSE_MOCK_EMPTY_FRAMES=true`: simulate camera outages and exercise fallback path
- `GRIDPULSE_MOCK_FRAME_COUNT=5`: max number of mock frames returned per request
- `GRIDPULSE_AUTO_SYNC_LIVE_EVENTS=true`: auto-hydrate events when app starts empty
- `GRIDPULSE_CSV_EVENTS_ENABLED=true`: enable CSV-backed event ingestion fallback
- `GRIDPULSE_UT_SPORTS_CSV_PATH=data/UT_Sports_Events.csv`: UT sports calendar CSV path
- `GRIDPULSE_VENUES_CAPACITY_CSV_PATH=data/venues_capacity.csv`: venue capacity lookup CSV path
- `GRIDPULSE_FACILITY_ENERGY_CSV_PATH=data/Facility_Energy_Usage.csv`: facility energy index CSV path
- `GRIDPULSE_COMPREHENSIVE_ENERGY_LOOKUP_CSV_PATH=data/comprehensive_energy_lookup_5deg.csv`: venue-temperature energy lookup CSV
- `GRIDPULSE_ENERGY_LOOKUP_ENABLED=true`: enable comprehensive CSV weather/intensity multipliers with fallback curve
- `GRIDPULSE_WEATHER_SOURCE=open_meteo`: live weather from Open-Meteo
- `GRIDPULSE_ERCOT_SOURCE=ercot_public_api`: use ERCOT Public Data API (`api.ercot.com`)
- `GRIDPULSE_ERCOT_SUBSCRIPTION_KEY=...`: ERCOT APIM subscription key
- `GRIDPULSE_ERCOT_ID_TOKEN=...`: ERCOT ID token (optional in config, required by ERCOT for authenticated calls)
- `GRIDPULSE_ERCOT_PUBLIC_EMIL_ID=NP6-905-CD`: EMIL product id
- `GRIDPULSE_ERCOT_PUBLIC_OPERATION=2d_agg_edc`: operation artifact path to fetch
- `GRIDPULSE_ERCOT_ENDPOINT_DISCOVERY=true`: discover artifact URL from product metadata before calling data endpoint
- `GRIDPULSE_ERCOT_USE_LEGACY_DASHBOARD_FALLBACK=false`: optionally fallback to older dashboard endpoint shape
- `GRIDPULSE_EIA_API_KEY=DEMO_KEY`: default no-cost key for EIA endpoint testing
- `GRIDPULSE_TICKETMASTER_API_KEY=...`: optional to ingest more live events in Austin
- `GRIDPULSE_DISPATCH_PRECHARGE_HOURS=2`: lead time for pre-charge recommendations
- `GRIDPULSE_CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`: local frontend origins

## Tests

```bash
cd backend
source .venv/bin/activate
pytest
```
