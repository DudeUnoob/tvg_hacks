# GridPulse Frontend (Layer 1-4 Canvas)

This frontend now runs a live, API-backed Layer 1-4 experience:

- Layer 1: event ingestion visibility + live sync controls
- Layer 2: crowd confirmation trigger + forecast confidence/attendance
- Layer 3: real-time **Mapbox** canvas, weather pressure test, urban overlays + 5/10-year simulation
- Layer 4: dispatch recommendations, reasoning trace, and dispatch payload preview
- Energy lookup integration: weather simulation + dispatch include backend-derived `energy_profile`, `weather_multiplier`, and venue match/source context

On first load, the UI calls `POST /events/sync-live`, then hydrates map state, events, dispatch data, overlays, and forecast context. Core map/dispatch data refresh periodically for a live demo feel.

## Quick start

```bash
cd frontend
npm install
npm run dev
```

Default app URL: `http://127.0.0.1:5173`.

## Backend dependency

Default backend URL: `http://127.0.0.1:8000`.

Copy environment template first:

```bash
cp .env.example .env.local
```

Then adjust values as needed:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_MAPBOX_TOKEN=your_mapbox_public_token
```

Notes:

- `VITE_API_BASE_URL` is optional; default is `http://127.0.0.1:8000`.
- `VITE_MAPBOX_TOKEN` is required for full Layer 3 map rendering.
- If `VITE_MAPBOX_TOKEN` is missing, the app gracefully falls back to an interactive non-map event list.

## Demo runbook

Terminal 1:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Terminal 2:

```bash
cd frontend
npm install
npm run dev
```
