import { useCallback, useEffect, useMemo, useState } from "react";

import {
  confirmCrowd,
  fetchActiveDispatch,
  fetchActiveEvents,
  fetchForecast,
  fetchMapState,
  fetchUrbanOverlays,
  simulateUrbanImpact,
  simulateWeather,
  syncLiveEvents,
} from "./api/client";
import { DispatchPanel } from "./components/DispatchPanel";
import { DispatchTerminal } from "./components/DispatchTerminal";
import { Footer } from "./components/Footer";
import { HeroSection } from "./components/HeroSection";
import { LiveFeedDashboard } from "./components/LiveFeedDashboard";
import { MapCanvas } from "./components/MapCanvas";
import { TelemetryBar } from "./components/TelemetryBar";
import { UrbanOverlayToggle } from "./components/UrbanOverlayToggle";
import type {
  CrowdSignalResponse,
  DispatchRecommendation,
  EventResponse,
  ForecastResponse,
  MapStateResponse,
  UrbanOverlaysResponse,
  UrbanSimulationResponse,
  WeatherSimulationResponse,
} from "./types/api";

const CORE_REFRESH_INTERVAL_MS = 60_000;

function toErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "Unknown error";
}

export default function App() {
  const [mapState, setMapState] = useState<MapStateResponse | null>(null);
  const [activeEvents, setActiveEvents] = useState<EventResponse[]>([]);
  const [dispatchRecommendations, setDispatchRecommendations] = useState<DispatchRecommendation[]>([]);
  const [urbanOverlays, setUrbanOverlays] = useState<UrbanOverlaysResponse | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [crowdSignal, setCrowdSignal] = useState<CrowdSignalResponse | null>(null);
  const [weatherSimulation, setWeatherSimulation] = useState<WeatherSimulationResponse | null>(null);
  const [urbanSimulation, setUrbanSimulation] = useState<UrbanSimulationResponse | null>(null);

  const [showOverlays, setShowOverlays] = useState(true);
  const [temperatureF, setTemperatureF] = useState(84);

  const [coreLoading, setCoreLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [crowdLoading, setCrowdLoading] = useState(false);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [urbanLoading, setUrbanLoading] = useState(false);

  const [coreError, setCoreError] = useState<string | null>(null);
  const [syncWarning, setSyncWarning] = useState<string | null>(null);
  const [crowdError, setCrowdError] = useState<string | null>(null);
  const [weatherError, setWeatherError] = useState<string | null>(null);
  const [urbanError, setUrbanError] = useState<string | null>(null);

  const refreshCoreData = useCallback(
    async ({ sync = false, silent = false }: { sync?: boolean; silent?: boolean } = {}) => {
      if (!silent) {
        setCoreLoading(true);
      }
      setCoreError(null);

      if (sync) {
        setSyncing(true);
        setSyncWarning(null);
        try {
          await syncLiveEvents(false);
        } catch (error) {
          setSyncWarning(`Live sync warning: ${toErrorMessage(error)}`);
        } finally {
          setSyncing(false);
        }
      }

      try {
        const [nextMapState, nextActiveEvents, nextDispatch, nextOverlays] = await Promise.all([
          fetchMapState(),
          fetchActiveEvents(),
          fetchActiveDispatch(),
          fetchUrbanOverlays(),
        ]);

        setMapState(nextMapState);
        setActiveEvents(nextActiveEvents);
        setDispatchRecommendations(nextDispatch);
        setUrbanOverlays(nextOverlays);
        setSelectedEventId((current) => {
          if (current && nextMapState.events.some((event) => event.event_id === current)) {
            return current;
          }
          return (
            nextMapState.events[0]?.event_id ??
            nextActiveEvents[0]?.event_id ??
            nextDispatch[0]?.event_id ??
            null
          );
        });
      } catch (error) {
        setCoreError(toErrorMessage(error));
      } finally {
        if (!silent) {
          setCoreLoading(false);
        }
      }
    },
    [],
  );

  useEffect(() => {
    void refreshCoreData({ sync: true });
  }, [refreshCoreData]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      void refreshCoreData({ silent: true });
    }, CORE_REFRESH_INTERVAL_MS);
    return () => window.clearInterval(intervalId);
  }, [refreshCoreData]);

  useEffect(() => {
    const mapEvents = mapState?.events ?? [];
    if (!mapEvents.length) {
      return;
    }
    if (!selectedEventId || !mapEvents.some((event) => event.event_id === selectedEventId)) {
      setSelectedEventId(mapEvents[0].event_id);
    }
  }, [mapState, selectedEventId]);

  useEffect(() => {
    if (!selectedEventId) {
      setForecast(null);
      setCrowdSignal(null);
      return;
    }

    let cancelled = false;
    setCrowdError(null);
    setCrowdSignal(null);

    const loadForecast = async () => {
      try {
        const nextForecast = await fetchForecast(selectedEventId);
        if (!cancelled) {
          setForecast(nextForecast);
        }
      } catch (error) {
        if (!cancelled) {
          setCrowdError(toErrorMessage(error));
        }
      }
    };

    void loadForecast();
    return () => {
      cancelled = true;
    };
  }, [selectedEventId]);

  useEffect(() => {
    if (!selectedEventId) {
      setWeatherSimulation(null);
      return;
    }

    let cancelled = false;
    const timeoutId = window.setTimeout(async () => {
      setWeatherLoading(true);
      setWeatherError(null);

      try {
        const nextSimulation = await simulateWeather(selectedEventId, temperatureF);
        if (!cancelled) {
          setWeatherSimulation(nextSimulation);
        }
      } catch (error) {
        if (!cancelled) {
          setWeatherSimulation(null);
          setWeatherError(toErrorMessage(error));
        }
      } finally {
        if (!cancelled) {
          setWeatherLoading(false);
        }
      }
    }, 250);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [selectedEventId, temperatureF]);

  const handleSelectEvent = useCallback((eventId: string) => {
    setSelectedEventId(eventId);
  }, []);

  const handleConfirmCrowd = useCallback(async () => {
    if (!selectedEventId) {
      return;
    }

    setCrowdLoading(true);
    setCrowdError(null);

    try {
      const nextSignal = await confirmCrowd(selectedEventId, { sample_size: 4 });
      setCrowdSignal(nextSignal);

      const [nextForecast, nextMapState, nextDispatch] = await Promise.all([
        fetchForecast(selectedEventId, true),
        fetchMapState(),
        fetchActiveDispatch(),
      ]);

      setForecast(nextForecast);
      setMapState(nextMapState);
      setDispatchRecommendations(nextDispatch);
    } catch (error) {
      setCrowdError(toErrorMessage(error));
    } finally {
      setCrowdLoading(false);
    }
  }, [selectedEventId]);

  const runUrbanSimulation = useCallback(
    async (horizonYears: number) => {
      setUrbanLoading(true);
      setUrbanError(null);

      try {
        const defaultProjectId = urbanOverlays?.capital_projects[0]?.project_id;
        const nextSimulation = await simulateUrbanImpact({
          project_id: defaultProjectId,
          horizon_years: horizonYears,
        });
        setUrbanSimulation(nextSimulation);
      } catch (error) {
        setUrbanError(toErrorMessage(error));
      } finally {
        setUrbanLoading(false);
      }
    },
    [urbanOverlays],
  );

  const selectedMapEvent = useMemo(() => {
    const mapEvents = mapState?.events ?? [];
    if (!mapEvents.length) {
      return null;
    }
    if (!selectedEventId) {
      return mapEvents[0];
    }
    return mapEvents.find((event) => event.event_id === selectedEventId) ?? mapEvents[0];
  }, [mapState, selectedEventId]);

  const selectedRecommendation = useMemo(() => {
    if (!dispatchRecommendations.length) {
      return null;
    }
    if (!selectedEventId) {
      return dispatchRecommendations[0];
    }
    return (
      dispatchRecommendations.find((recommendation) => recommendation.event_id === selectedEventId) ??
      dispatchRecommendations[0]
    );
  }, [dispatchRecommendations, selectedEventId]);

  const eventMetadataById = useMemo(() => {
    const lookup: Record<string, EventResponse> = {};
    for (const event of activeEvents) {
      lookup[event.event_id] = event;
    }
    return lookup;
  }, [activeEvents]);

  const urbanSimulationSummary = useMemo(() => {
    if (urbanLoading) {
      return "Running urban demand simulation...";
    }
    if (urbanError) {
      return `Urban simulation error: ${urbanError}`;
    }
    if (!urbanSimulation) {
      return "Run a 5-year or 10-year simulation to project neighborhood load and battery need.";
    }
    const { simulation } = urbanSimulation;
    return (
      `${simulation.scenario_name} (${simulation.horizon_years}y): projected ` +
      `${simulation.projected_load_mw.toFixed(2)} MW vs ${simulation.current_capacity_mw.toFixed(2)} MW capacity. ` +
      `Headroom ${simulation.transformer_headroom_mw.toFixed(2)} MW, stress ` +
      `${simulation.grid_stress_level.toUpperCase()}, recommended batteries ${simulation.recommended_battery_count.toLocaleString()}.`
    );
  }, [urbanError, urbanLoading, urbanSimulation]);

  const mapEvents = mapState?.events ?? [];
  const telemetryPrice = mapState?.ercot.price_mwh ?? 42.5;
  const telemetryLoad = mapState?.ercot.load_mw ?? 45_902;

  return (
    <div className="min-h-screen bg-dark w-full overflow-x-hidden selection:bg-olive/30 selection:text-white pb-0">
      <TelemetryBar price={telemetryPrice} load={telemetryLoad} />
      <HeroSection />

      <LiveFeedDashboard
        events={mapEvents}
        eventMetadataById={eventMetadataById}
        selectedEventId={selectedEventId}
        selectedEvent={selectedMapEvent}
        forecast={forecast}
        crowdSignal={crowdSignal}
        onSelectEvent={handleSelectEvent}
        onConfirmCrowd={handleConfirmCrowd}
        crowdLoading={crowdLoading}
        crowdError={crowdError}
        temperatureF={temperatureF}
        onTemperatureChange={setTemperatureF}
        onWorstCase={() => setTemperatureF(102)}
        weatherSimulation={weatherSimulation}
        weatherLoading={weatherLoading}
        weatherError={weatherError}
        weatherDisabled={!selectedEventId}
        loading={coreLoading}
      />

      <main className="relative z-20 max-w-[1440px] mx-auto px-6 mb-20">
        {(syncing || syncWarning || coreError) && (
          <div className="mb-6 rounded-sm border border-white/10 bg-black/35 p-3 font-mono text-xs text-grey-olive">
            {syncing ? "Syncing live events..." : null}
            {syncWarning ? ` ${syncWarning}` : null}
            {coreError ? ` Core data error: ${coreError}` : null}
          </div>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2">
            <MapCanvas
              events={mapEvents}
              selectedEventId={selectedEventId}
              onSelectEvent={handleSelectEvent}
              showOverlays={showOverlays}
              stations={urbanOverlays?.stations ?? []}
              capitalProjects={urbanOverlays?.capital_projects ?? []}
              zoningCorridors={urbanOverlays?.zoning_corridors ?? []}
              loading={coreLoading}
              error={coreError}
            />
          </div>

          <div className="space-y-6">
            <UrbanOverlayToggle
              showOverlays={showOverlays}
              stationCount={urbanOverlays?.stations.length ?? 0}
              projectCount={urbanOverlays?.capital_projects.length ?? 0}
              zoningCount={urbanOverlays?.zoning_corridors.length ?? 0}
              onToggleOverlays={setShowOverlays}
              onRunFiveYear={() => {
                void runUrbanSimulation(5);
              }}
              onRunTenYear={() => {
                void runUrbanSimulation(10);
              }}
              simulationSummary={urbanSimulationSummary}
              loading={urbanLoading}
              disabled={coreLoading}
              error={urbanError}
            />
            <DispatchPanel
              recommendations={dispatchRecommendations}
              selectedEventId={selectedEventId}
            />
          </div>
        </div>
      </main>

      <DispatchTerminal
        recommendation={selectedRecommendation}
        loading={coreLoading && dispatchRecommendations.length === 0}
        error={coreError}
      />
      <Footer />
    </div>
  );
}

