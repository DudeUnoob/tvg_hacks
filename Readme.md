# GridPulse

**Real-time AI energy simulator for Austin's power grid.**

Austin's grid can't see a 100,000-person football game coming. GridPulse fixes that — it fuses live event data, crowd intelligence from camera feeds, weather conditions, and urban planning projections into hyperlocal energy forecasts and battery dispatch commands.

Built for the [TVG Hacks](https://tvghacks.com) hackathon targeting Base Power's distributed battery fleet.

## How It Works

GridPulse runs on a four-layer architecture:

1. **Event Intelligence** — Ingests UT Austin athletics, Moody Center, Ticketmaster, and other event calendars. Each event gets a crowd estimate, geographic footprint, and dispersal timeline.

2. **VLM Crowd Confirmation** — Gemini Vision analyzes live Austin traffic camera feeds to estimate real-time parking lot fill rates, dynamically adjusting crowd forecasts with confidence scores.

3. **Simulation Canvas** — An interactive map of Austin with three modes:
   - *Real-Time* — Active events as pulsing nodes, crowd density heat maps, live ERCOT price ticker, demand wave propagation by zip code.
   - *Weather Stress Test* — Slide temperature from 50°F to 110°F and watch projected post-event AC load shift neighborhood by neighborhood.
   - *Urban Planning* — Project Connect light rail stations, capital improvement projects, and zoning corridors overlaid on the map. Click any project to simulate 5- and 10-year energy demand impact.

4. **Dispatch Engine** — Outputs zip-code-level battery pre-charge commands with plain-English reasoning traces and revenue estimates.

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React, TypeScript, Vite, Mapbox GL, Tailwind CSS |
| Backend | Python, FastAPI |
| VLM | Google Gemini (multimodal) |
| Data | ERCOT historical load, OpenWeatherMap, TXDOT camera feeds, Austin open data |

## Getting Started

### Backend

```bash
cd backend
cp .env.example .env   # fill in your API keys
pip install -e .
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The frontend runs on `http://localhost:5173` and the backend API on `http://localhost:8000`.

## Team

- **Damodar Kamani**
- **Rehan Mollick**
- **Kaustubh Kondapalli**
- **Mehak Arora**
