# GridPulse Frontend (Minimal Layer 3 + Layer 4 UI)

This frontend is a minimal demo canvas for the next GridPulse sections:

- Layer 3 Real-Time mode: event map canvas + ERCOT ticker
- Layer 3 Weather Pressure Test mode: temperature slider and projected load impacts
- Layer 3 Urban Planning mode: overlay counts and 5/10-year simulation trigger
- Layer 4 mode: ranked dispatch recommendations panel

## Quick start

```bash
cd frontend
npm install
npm run dev
```

The app runs by default at `http://127.0.0.1:5173`.

## Backend dependency

The frontend expects backend API at `http://127.0.0.1:8000` by default.

To override:

```bash
echo "VITE_API_BASE_URL=http://127.0.0.1:8000" > .env.local
```

## Demo runbook (two terminals)

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

If no events appear, ingest sample data from backend terminal:

```bash
curl -X POST "http://127.0.0.1:8000/events/ingest" \
  -H "Content-Type: application/json" \
  --data @tests/fixtures/sample_events.json
```
