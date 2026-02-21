import { useEffect, useMemo, useRef } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

import type {
  CapitalProject,
  MapEventState,
  UrbanStation,
  ZoningCorridor,
} from "../types/api";

interface MapCanvasProps {
  events: MapEventState[];
  selectedEventId: string | null;
  onSelectEvent: (eventId: string) => void;
  showOverlays: boolean;
  stations: UrbanStation[];
  capitalProjects: CapitalProject[];
  zoningCorridors: ZoningCorridor[];
  loading?: boolean;
  error?: string | null;
}

const AUSTIN_CENTER: [number, number] = [-97.7431, 30.2672];
const mapboxToken = import.meta.env.VITE_MAPBOX_TOKEN as string | undefined;

function clearMarkers(markers: mapboxgl.Marker[]): void {
  for (const marker of markers) {
    marker.remove();
  }
  markers.length = 0;
}

function createPointMarker({
  size,
  color,
  borderColor,
  pulse,
  title,
}: {
  size: number;
  color: string;
  borderColor: string;
  pulse?: boolean;
  title: string;
}): HTMLButtonElement {
  const element = document.createElement("button");
  element.type = "button";
  element.title = title;
  element.style.width = `${size}px`;
  element.style.height = `${size}px`;
  element.style.borderRadius = "9999px";
  element.style.backgroundColor = color;
  element.style.border = `2px solid ${borderColor}`;
  element.style.boxShadow = `0 0 10px ${borderColor}`;
  element.style.cursor = "pointer";
  if (pulse) {
    element.animate(
      [
        { transform: "scale(1)", opacity: "0.8" },
        { transform: "scale(1.15)", opacity: "1" },
        { transform: "scale(1)", opacity: "0.8" },
      ],
      { duration: 1700, iterations: Number.POSITIVE_INFINITY },
    );
  }
  return element;
}

export function MapCanvas({
  events,
  selectedEventId,
  onSelectEvent,
  showOverlays,
  stations,
  capitalProjects,
  zoningCorridors,
  loading = false,
  error = null,
}: MapCanvasProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const eventMarkersRef = useRef<mapboxgl.Marker[]>([]);
  const overlayMarkersRef = useRef<mapboxgl.Marker[]>([]);

  const selectedEvent = useMemo(
    () => events.find((event) => event.event_id === selectedEventId) ?? null,
    [events, selectedEventId],
  );

  useEffect(() => {
    if (!mapboxToken || !mapContainerRef.current || mapRef.current) {
      return;
    }

    mapboxgl.accessToken = mapboxToken;
    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: AUSTIN_CENTER,
      zoom: 10.6,
      pitch: 36,
      antialias: true,
    });
    map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), "top-right");
    mapRef.current = map;

    return () => {
      clearMarkers(eventMarkersRef.current);
      clearMarkers(overlayMarkersRef.current);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) {
      return;
    }

    clearMarkers(eventMarkersRef.current);
    for (const event of events) {
      const selected = event.event_id === selectedEventId;
      const size = 14 + event.heat_intensity * 22;
      const markerElement = createPointMarker({
        size,
        color: selected ? "#FF5A7A" : "#4F5D2F",
        borderColor: selected ? "#CFD6EA" : "#7D7E75",
        pulse: true,
        title: `${event.name} (${event.adjusted_attendance.toLocaleString()} est.)`,
      });
      markerElement.addEventListener("click", () => onSelectEvent(event.event_id));

      const marker = new mapboxgl.Marker({ element: markerElement })
        .setLngLat([event.longitude, event.latitude])
        .addTo(map);
      eventMarkersRef.current.push(marker);
    }
  }, [events, onSelectEvent, selectedEventId]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) {
      return;
    }

    clearMarkers(overlayMarkersRef.current);
    if (!showOverlays) {
      return;
    }

    for (const station of stations) {
      const marker = new mapboxgl.Marker({
        element: createPointMarker({
          size: 10,
          color: "#00E5FF",
          borderColor: "#CFD6EA",
          title: `Station: ${station.name} (${station.corridor})`,
        }),
      })
        .setLngLat([station.longitude, station.latitude])
        .addTo(map);
      overlayMarkersRef.current.push(marker);
    }

    for (const project of capitalProjects) {
      const element = document.createElement("div");
      element.title = `Project: ${project.name}`;
      element.style.width = "12px";
      element.style.height = "12px";
      element.style.transform = "rotate(45deg)";
      element.style.backgroundColor = "#423629";
      element.style.border = "2px solid #CFD6EA";
      element.style.boxShadow = "0 0 10px rgba(66,54,41,0.9)";
      const marker = new mapboxgl.Marker({ element })
        .setLngLat([project.longitude, project.latitude])
        .addTo(map);
      overlayMarkersRef.current.push(marker);
    }

    for (const corridor of zoningCorridors) {
      const marker = new mapboxgl.Marker({
        element: createPointMarker({
          size: 9,
          color: "#0A0A0A",
          borderColor: "#4F5D2F",
          title: `Zoning: ${corridor.name} (${corridor.zoning_type})`,
        }),
      })
        .setLngLat([corridor.longitude, corridor.latitude])
        .addTo(map);
      overlayMarkersRef.current.push(marker);
    }
  }, [capitalProjects, showOverlays, stations, zoningCorridors]);

  useEffect(() => {
    if (!mapRef.current || !selectedEvent) {
      return;
    }
    mapRef.current.flyTo({
      center: [selectedEvent.longitude, selectedEvent.latitude],
      duration: 700,
      essential: true,
      zoom: Math.max(mapRef.current.getZoom(), 11),
    });
  }, [selectedEvent]);

  if (!mapboxToken) {
    return (
      <section className="tech-panel border border-white/10 rounded-xl p-5">
        <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-4">
          <h2 className="font-mono text-sm tracking-widest text-[#00E5FF]">Layer 3: Real-Time Canvas</h2>
          <span className="font-mono text-xs text-white/50">{events.length} event(s)</span>
        </div>
        <div className="rounded border border-white/10 bg-black/35 p-4 text-sm text-white/70">
          <p className="mb-3 text-red-200">
            Mapbox token missing. Set `VITE_MAPBOX_TOKEN` in `frontend/.env.local` to enable live map rendering.
          </p>
          <p className="mb-3 text-white/60">Fallback event list remains interactive:</p>
          <ul className="space-y-2">
            {events.map((event) => (
              <li key={event.event_id}>
                <button
                  className={`w-full rounded border px-3 py-2 text-left text-xs font-mono ${
                    selectedEventId === event.event_id
                      ? "border-[#00E5FF]/60 bg-[#00E5FF]/10 text-[#00E5FF]"
                      : "border-white/10 bg-black/20 text-white/70 hover:bg-black/35"
                  }`}
                  onClick={() => onSelectEvent(event.event_id)}
                  type="button"
                >
                  {event.name} · {event.adjusted_attendance.toLocaleString()} · heat {event.heat_intensity.toFixed(2)}
                </button>
              </li>
            ))}
            {!events.length ? <li className="text-white/50">No events available.</li> : null}
          </ul>
        </div>
      </section>
    );
  }

  return (
    <section className="tech-panel border border-white/10 rounded-xl p-5">
      <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-4">
        <h2 className="font-mono text-sm tracking-widest text-[#00E5FF]">Layer 3: Real-Time Canvas</h2>
        <span className="font-mono text-xs text-white/50">{events.length} event(s)</span>
      </div>

      <div className="relative h-[560px] rounded border border-white/10 overflow-hidden bg-black/30">
        <div className="absolute inset-0" ref={mapContainerRef} />
        {loading ? (
          <div className="absolute top-3 left-3 rounded bg-black/60 px-3 py-1 text-[11px] font-mono text-grey-olive">
            Hydrating live map state...
          </div>
        ) : null}
        {error ? (
          <div className="absolute top-3 left-3 rounded bg-red-900/40 px-3 py-1 text-[11px] font-mono text-red-100">
            {error}
          </div>
        ) : null}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-3 text-[11px] font-mono text-white/55">
        <span>Event nodes: heat intensity + attendance</span>
        <span>•</span>
        <span>Blue: stations</span>
        <span>•</span>
        <span>Taupe: capital projects</span>
        <span>•</span>
        <span>Olive ring: zoning corridors</span>
      </div>
    </section>
  );
}
