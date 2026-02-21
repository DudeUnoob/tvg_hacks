import { useEffect, useMemo, useState } from "react";

import {
  fetchActiveDispatch,
  fetchMapState,
  fetchUrbanOverlays,
  simulateUrbanImpact,
  simulateWeather,
} from "./api/client";
import { DispatchPanel } from "./components/DispatchPanel";
import { MapCanvas } from "./components/MapCanvas";
import { UrbanOverlayToggle } from "./components/UrbanOverlayToggle";
import { WeatherSlider } from "./components/WeatherSlider";
import type {
  DispatchRecommendation,
  MapStateResponse,
  UrbanOverlaysResponse,
  WeatherSimulationResponse,
} from "./types/api";

const POLL_INTERVAL_MS = 15_000;

export default function App() {
  const [mapState, setMapState] = useState<MapStateResponse | null>(null);
  const [overlays, setOverlays] = useState<UrbanOverlaysResponse | null>(null);
  const [dispatchRecommendations, setDispatchRecommendations] = useState<DispatchRecommendation[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [temperatureF, setTemperatureF] = useState<number>(92);
  const [weatherSimulation, setWeatherSimulation] = useState<WeatherSimulationResponse | null>(null);
  const [showOverlays, setShowOverlays] = useState<boolean>(true);
  const [urbanSimulationSummary, setUrbanSimulationSummary] = useState<string>(
    "Run a 5-year or 10-year simulation to estimate neighborhood capacity stress.",
  );
  const [error, setError] = useState<string>("");

  const selectedEvent = useMemo(
    () => mapState?.events.find((event) => event.event_id === selectedEventId) ?? null,
    [mapState, selectedEventId],
  );

  const refreshMapAndDispatch = async () => {
    try {
      const [nextMapState, nextDispatch] = await Promise.all([fetchMapState(), fetchActiveDispatch()]);
      setMapState(nextMapState);
      setDispatchRecommendations(nextDispatch);
      setError("");

      if (!selectedEventId && nextMapState.events.length > 0) {
        setSelectedEventId(nextMapState.events[0].event_id);
      }
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Failed to refresh GridPulse state.");
    }
  };

  useEffect(() => {
    refreshMapAndDispatch();
    const timer = window.setInterval(refreshMapAndDispatch, POLL_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    fetchUrbanOverlays()
      .then((response) => setOverlays(response))
      .catch((nextError) =>
        setError(nextError instanceof Error ? nextError.message : "Failed to load urban overlays."),
      );
  }, []);

  useEffect(() => {
    if (!selectedEventId) {
      setWeatherSimulation(null);
      return;
    }

    simulateWeather(selectedEventId, temperatureF)
      .then((response) => setWeatherSimulation(response))
      .catch((nextError) =>
        setError(nextError instanceof Error ? nextError.message : "Failed to run weather simulation."),
      );
  }, [selectedEventId, temperatureF]);

  const runUrbanSimulation = async (horizonYears: 5 | 10) => {
    try {
      const defaultProject = overlays?.capital_projects[0];
      const response = await simulateUrbanImpact(
        defaultProject
          ? { project_id: defaultProject.project_id, horizon_years: horizonYears }
          : {
              project_name: "SimCity hypothetical mixed-use build",
              horizon_years: horizonYears,
              building_units: 850,
              commercial_sqft: 220000,
            },
      );
      const sim = response.simulation;
      setUrbanSimulationSummary(
        `${sim.scenario_name} (${sim.horizon_years}y): projected ${sim.projected_load_mw.toFixed(2)} MW, ` +
          `headroom ${sim.transformer_headroom_mw.toFixed(2)} MW, batteries ${sim.recommended_battery_count}, ` +
          `stress ${sim.grid_stress_level}.`,
      );
      setError("");
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Urban simulation failed.");
    }
  };

  return (
    <main className="app">
      <header className="header">
        <div>
          <h1>GridPulse Layer 3 + Layer 4 Demo</h1>
          <p className="muted">Real-Time map, weather pressure testing, urban overlays, dispatch outputs.</p>
        </div>
        <div className="ticker">
          <div>ERCOT price: ${mapState?.ercot.price_mwh.toFixed(2) ?? "--"} / MWh</div>
          <div>ERCOT load: {mapState?.ercot.load_mw.toFixed(1) ?? "--"} MW</div>
        </div>
      </header>

      {error ? <p className="error">{error}</p> : null}

      <section className="grid">
        <div className="stack">
          <MapCanvas
            events={mapState?.events ?? []}
            onSelectEvent={setSelectedEventId}
            selectedEventId={selectedEventId}
          />

          <WeatherSlider
            disabled={!selectedEvent}
            onTemperatureChange={setTemperatureF}
            onWorstCase={() => setTemperatureF(102)}
            temperatureF={temperatureF}
          />

          <section className="card">
            <div className="card-header">
              <h2>Weather Simulation Output</h2>
              <span className="muted">{selectedEvent?.name ?? "No event selected"}</span>
            </div>
            <p className="muted">
              Multiplier: {weatherSimulation?.weather_multiplier.toFixed(2) ?? "--"} | Peak delta:{" "}
              {weatherSimulation?.projected_peak_mw.toFixed(3) ?? "--"} MW
            </p>
            <ul>
              {(weatherSimulation?.zip_projections ?? []).map((item) => (
                <li key={item.zip_code}>
                  {item.zip_code}: +{item.projected_load_delta_mw.toFixed(3)} MW
                </li>
              ))}
            </ul>
          </section>
        </div>

        <div className="stack">
          <UrbanOverlayToggle
            onRunFiveYear={() => runUrbanSimulation(5)}
            onRunTenYear={() => runUrbanSimulation(10)}
            onToggleOverlays={setShowOverlays}
            projectCount={showOverlays ? overlays?.capital_projects.length ?? 0 : 0}
            showOverlays={showOverlays}
            simulationSummary={urbanSimulationSummary}
            stationCount={showOverlays ? overlays?.stations.length ?? 0 : 0}
            zoningCount={showOverlays ? overlays?.zoning_corridors.length ?? 0 : 0}
          />

          <DispatchPanel
            recommendations={dispatchRecommendations}
            selectedEventId={selectedEventId}
          />
        </div>
      </section>
    </main>
  );
}
