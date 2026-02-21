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
- `POST /layer3/simulate`: weather pressure test for an event (`event_id`, `temperature_f`)
- `GET /layer3/urban-overlays`: Project Connect stations, capital projects, zoning corridors
- `POST /layer3/urban-simulate`: 5/10-year urban impact simulation

## Layer 4 endpoints

- `GET /layer4/dispatch/active`: ranked dispatch recommendations for active events
- `GET /layer4/dispatch/{event_id}`: dispatch recommendation for a specific event

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

## Configuration

Environment variables are prefixed with `GRIDPULSE_`:

- `GRIDPULSE_MOCK_MODE=true`: use deterministic mock VLM estimates
- `GRIDPULSE_GEMINI_API_KEY`: enable real Gemini API calls when mock mode is `false`
- `GRIDPULSE_MOCK_EMPTY_FRAMES=true`: simulate camera outages and exercise fallback path
- `GRIDPULSE_MOCK_FRAME_COUNT=5`: max number of mock frames returned per request
- `GRIDPULSE_WEATHER_SOURCE=mock`: weather data mode
- `GRIDPULSE_ERCOT_SOURCE=mock`: ERCOT data mode
- `GRIDPULSE_DISPATCH_PRECHARGE_HOURS=2`: lead time for pre-charge recommendations
- `GRIDPULSE_CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`: local frontend origins

## Tests

```bash
cd backend
source .venv/bin/activate
pytest
```
