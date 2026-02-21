# GridPulse Backend (Layer 1 + Layer 2 MVP)

This service implements the first two GridPulse layers from `app_context/tvg.md`:

- Layer 1: Event ingestion + baseline attendance/dispersal estimation
- Layer 2: VLM-style crowd confirmation from camera frames with confidence and fallback handling

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

## Core endpoints

- `POST /events/ingest`: ingest raw events and normalize to canonical fields
- `GET /events`: list all ingested events
- `GET /events/active`: list currently active events
- `POST /crowd/confirm/{event_id}`: run crowd confirmation using frame provider + VLM adapter
- `GET /forecasts/{event_id}`: return fused baseline + VLM forecast

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

## Configuration

Environment variables are prefixed with `GRIDPULSE_`:

- `GRIDPULSE_MOCK_MODE=true`: use deterministic mock VLM estimates
- `GRIDPULSE_GEMINI_API_KEY`: enable real Gemini API calls when mock mode is `false`
- `GRIDPULSE_MOCK_EMPTY_FRAMES=true`: simulate camera outages and exercise fallback path
- `GRIDPULSE_MOCK_FRAME_COUNT=5`: max number of mock frames returned per request

## Tests

```bash
cd backend
source .venv/bin/activate
pytest
```
