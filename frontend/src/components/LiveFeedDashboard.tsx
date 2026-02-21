import { ThreatList } from "./ThreatList";
import { VisionCamera } from "./VisionCamera";
import { WeatherStress } from "./WeatherStress";
import type {
  CrowdSignalResponse,
  EventResponse,
  ForecastResponse,
  MapEventState,
  WeatherSimulationResponse,
} from "../types/api";

interface LiveFeedDashboardProps {
  events: MapEventState[];
  eventMetadataById: Record<string, EventResponse>;
  selectedEventId: string | null;
  selectedEvent: MapEventState | null;
  forecast: ForecastResponse | null;
  crowdSignal: CrowdSignalResponse | null;
  onSelectEvent: (eventId: string) => void;
  onConfirmCrowd: () => void;
  crowdLoading: boolean;
  crowdError: string | null;
  temperatureF: number;
  onTemperatureChange: (temperatureF: number) => void;
  onWorstCase: () => void;
  weatherSimulation: WeatherSimulationResponse | null;
  weatherLoading: boolean;
  weatherError: string | null;
  weatherDisabled: boolean;
  loading: boolean;
}

export function LiveFeedDashboard({
  events,
  eventMetadataById,
  selectedEventId,
  selectedEvent,
  forecast,
  crowdSignal,
  onSelectEvent,
  onConfirmCrowd,
  crowdLoading,
  crowdError,
  temperatureF,
  onTemperatureChange,
  onWorstCase,
  weatherSimulation,
  weatherLoading,
  weatherError,
  weatherDisabled,
  loading,
}: LiveFeedDashboardProps) {
  return (
    <section className="relative z-20 max-w-[1440px] mx-auto px-6 -mt-32 mb-16">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ThreatList
          events={events}
          eventMetadataById={eventMetadataById}
          selectedEventId={selectedEventId}
          onSelectEvent={onSelectEvent}
          loading={loading}
        />
        <VisionCamera
          selectedEvent={selectedEvent}
          forecast={forecast}
          crowdSignal={crowdSignal}
          onConfirmCrowd={onConfirmCrowd}
          confirming={crowdLoading}
          error={crowdError}
        />
        <WeatherStress
          temperatureF={temperatureF}
          onTemperatureChange={onTemperatureChange}
          onWorstCase={onWorstCase}
          projectedPeakMw={weatherSimulation?.projected_peak_mw ?? null}
          weatherMultiplier={weatherSimulation?.weather_multiplier ?? null}
          loading={weatherLoading}
          disabled={weatherDisabled}
          error={weatherError}
        />
      </div>
    </section>
  );
}
