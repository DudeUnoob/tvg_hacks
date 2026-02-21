# GridPulse Frontend (Layer 1-4 Canvas)

This frontend is wired to backend APIs for all available layers:

- Layer 1: event ingestion visibility + live sync controls
- Layer 2: crowd confirmation trigger + forecast confidence/attendance
- Layer 3: real-time map, weather pressure test, urban overlay + 5/10-year simulation
- Layer 4: dispatch recommendations, reasoning trace, and dispatch payload preview
- Energy lookup integration: weather simulation + dispatch include backend-derived `energy_profile`, `weather_multiplier`, and venue match/source context

On first load, the UI attempts `POST /events/sync-live`, then hydrates map state, events, forecasts, overlays, and dispatch data.

## Quick start

```bash
cd frontend
npm install
npm run dev
```

Default app URL: `http://127.0.0.1:5173`.

## Backend dependency

Default backend URL: `http://127.0.0.1:8000`.

Override API base:

```bash
echo "VITE_API_BASE_URL=http://127.0.0.1:8000" > .env.local
```

Optional Mapbox token override:

```bash
echo "VITE_MAPBOX_TOKEN=your_mapbox_token" >> .env.local
```

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
