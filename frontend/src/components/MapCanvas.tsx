import { useEffect, useMemo, useRef, useState } from "react";
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

const EVENT_SOURCE_ID = "events-source";
const EVENT_HEAT_LAYER_ID = "events-heat-layer";
const EVENT_GLOW_LAYER_ID = "events-glow-layer";
const EVENT_POINT_LAYER_ID = "events-point-layer";
const EVENT_SELECTED_LAYER_ID = "events-selected-layer";
const STATION_SOURCE_ID = "stations-source";
const STATION_LAYER_ID = "stations-layer";
const PROJECT_SOURCE_ID = "projects-source";
const PROJECT_LAYER_ID = "projects-layer";
const CORRIDOR_SOURCE_ID = "corridors-source";
const CORRIDOR_HEAT_LAYER_ID = "corridors-heat-layer";
const CORRIDOR_POINT_LAYER_ID = "corridors-point-layer";

type EventFeatureProps = {
  event_id: string;
  name: string;
  venue: string;
  adjusted_attendance: number;
  baseline_attendance: number;
  heat_intensity: number;
  confidence: number;
  weather_multiplier: number;
  projected_dispersal_peak: string;
};

type OverlayFeatureProps = {
  label: string;
  detail: string;
  magnitude: number;
};

function isValidLngLat(longitude: number, latitude: number): boolean {
  return (
    Number.isFinite(longitude) &&
    Number.isFinite(latitude) &&
    Math.abs(longitude) <= 180 &&
    Math.abs(latitude) <= 90
  );
}

function toEventFeatureCollection(
  events: MapEventState[],
): GeoJSON.FeatureCollection<GeoJSON.Point, EventFeatureProps> {
  return {
    type: "FeatureCollection",
    features: events
      .filter((event) => isValidLngLat(event.longitude, event.latitude))
      .map((event) => ({
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [event.longitude, event.latitude],
        },
        properties: {
          event_id: event.event_id,
          name: event.name,
          venue: event.venue,
          adjusted_attendance: event.adjusted_attendance,
          baseline_attendance: event.baseline_attendance,
          heat_intensity: event.heat_intensity,
          confidence: event.confidence,
          weather_multiplier: event.weather_multiplier,
          projected_dispersal_peak: event.projected_dispersal_peak,
        },
      })),
  };
}

function toStationFeatureCollection(
  stations: UrbanStation[],
): GeoJSON.FeatureCollection<GeoJSON.Point, OverlayFeatureProps> {
  return {
    type: "FeatureCollection",
    features: stations
      .filter((station) => isValidLngLat(station.longitude, station.latitude))
      .map((station) => ({
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [station.longitude, station.latitude],
        },
        properties: {
          label: station.name,
          detail: station.corridor,
          magnitude: 1,
        },
      })),
  };
}

function toProjectFeatureCollection(
  capitalProjects: CapitalProject[],
): GeoJSON.FeatureCollection<GeoJSON.Point, OverlayFeatureProps> {
  return {
    type: "FeatureCollection",
    features: capitalProjects
      .filter((project) => isValidLngLat(project.longitude, project.latitude))
      .map((project) => ({
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [project.longitude, project.latitude],
        },
        properties: {
          label: project.name,
          detail: project.status,
          magnitude: project.estimated_budget_usd,
        },
      })),
  };
}

function toCorridorFeatureCollection(
  zoningCorridors: ZoningCorridor[],
): GeoJSON.FeatureCollection<GeoJSON.Point, OverlayFeatureProps> {
  return {
    type: "FeatureCollection",
    features: zoningCorridors
      .filter((corridor) => isValidLngLat(corridor.longitude, corridor.latitude))
      .map((corridor) => ({
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [corridor.longitude, corridor.latitude],
        },
        properties: {
          label: corridor.name,
          detail: corridor.zoning_type,
          magnitude: corridor.density_multiplier,
        },
      })),
  };
}

function upsertGeoJsonSource(
  map: mapboxgl.Map,
  sourceId: string,
  data: GeoJSON.FeatureCollection<GeoJSON.Point>,
): void {
  const existingSource = map.getSource(sourceId) as mapboxgl.GeoJSONSource | undefined;
  if (existingSource) {
    existingSource.setData(data);
    return;
  }
  map.addSource(sourceId, { type: "geojson", data });
}

function readNumber(value: unknown, fallback = 0): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return fallback;
}

function readText(value: unknown, fallback = "N/A"): string {
  if (typeof value === "string" && value.trim()) {
    return value;
  }
  return fallback;
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
  const popupRef = useRef<mapboxgl.Popup | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);

  const selectedEvent = useMemo(
    () => events.find((event) => event.event_id === selectedEventId) ?? null,
    [events, selectedEventId],
  );

  useEffect(() => {
    if (!mapboxToken?.trim() || !mapContainerRef.current || mapRef.current) {
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
    popupRef.current = new mapboxgl.Popup({
      closeButton: false,
      closeOnClick: false,
      offset: 18,
      className: "font-mono text-[11px]",
    });
    map.on("load", () => {
      setMapReady(true);
      setMapError(null);
      map.resize();
    });
    map.on("error", (errorEvent) => {
      const detail =
        errorEvent.error instanceof Error && errorEvent.error.message
          ? errorEvent.error.message
          : "Map rendering failed. Verify style/network access and reload.";
      setMapError(detail);
    });
    const resizeTimeout = window.setTimeout(() => {
      map.resize();
    }, 120);
    mapRef.current = map;

    return () => {
      window.clearTimeout(resizeTimeout);
      setMapReady(false);
      popupRef.current?.remove();
      popupRef.current = null;
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!mapContainerRef.current) {
      return;
    }

    const resizeObserver = new ResizeObserver(() => {
      mapRef.current?.resize();
    });
    resizeObserver.observe(mapContainerRef.current);

    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) {
      return;
    }

    upsertGeoJsonSource(map, EVENT_SOURCE_ID, toEventFeatureCollection(events));
    upsertGeoJsonSource(map, STATION_SOURCE_ID, toStationFeatureCollection(stations));
    upsertGeoJsonSource(map, PROJECT_SOURCE_ID, toProjectFeatureCollection(capitalProjects));
    upsertGeoJsonSource(map, CORRIDOR_SOURCE_ID, toCorridorFeatureCollection(zoningCorridors));

    if (!map.getLayer(EVENT_HEAT_LAYER_ID)) {
      map.addLayer({
        id: EVENT_HEAT_LAYER_ID,
        type: "heatmap",
        source: EVENT_SOURCE_ID,
        maxzoom: 14,
        paint: {
          "heatmap-weight": [
            "interpolate",
            ["linear"],
            ["coalesce", ["to-number", ["get", "adjusted_attendance"]], 0],
            0,
            0,
            10_000,
            0.4,
            60_000,
            1,
          ],
          "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 6, 0.6, 12, 1.4],
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0,
            "rgba(8, 12, 22, 0)",
            0.2,
            "rgba(0, 229, 255, 0.30)",
            0.4,
            "rgba(125, 126, 117, 0.45)",
            0.6,
            "rgba(244, 167, 66, 0.55)",
            0.8,
            "rgba(255, 90, 122, 0.75)",
            1,
            "rgba(255, 52, 86, 0.9)",
          ],
          "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 6, 14, 10, 32, 13, 56],
          "heatmap-opacity": 0.72,
        },
      });
    }

    if (!map.getLayer(EVENT_GLOW_LAYER_ID)) {
      map.addLayer({
        id: EVENT_GLOW_LAYER_ID,
        type: "circle",
        source: EVENT_SOURCE_ID,
        minzoom: 8,
        paint: {
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["coalesce", ["to-number", ["get", "adjusted_attendance"]], 0],
            0,
            8,
            10_000,
            14,
            80_000,
            32,
          ],
          "circle-color": "#FF5A7A",
          "circle-opacity": 0.18,
          "circle-blur": 0.75,
        },
      });
    }

    if (!map.getLayer(EVENT_POINT_LAYER_ID)) {
      map.addLayer({
        id: EVENT_POINT_LAYER_ID,
        type: "circle",
        source: EVENT_SOURCE_ID,
        minzoom: 8,
        paint: {
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["coalesce", ["to-number", ["get", "heat_intensity"]], 0.1],
            0.1,
            5,
            1,
            12,
          ],
          "circle-color": [
            "interpolate",
            ["linear"],
            ["coalesce", ["to-number", ["get", "heat_intensity"]], 0.1],
            0.1,
            "#4F5D2F",
            0.45,
            "#B08B5E",
            0.7,
            "#F59E0B",
            1,
            "#FF5A7A",
          ],
          "circle-stroke-color": "#CFD6EA",
          "circle-stroke-width": 1.3,
          "circle-opacity": 0.94,
        },
      });
    }

    if (!map.getLayer(EVENT_SELECTED_LAYER_ID)) {
      map.addLayer({
        id: EVENT_SELECTED_LAYER_ID,
        type: "circle",
        source: EVENT_SOURCE_ID,
        minzoom: 8,
        paint: {
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["coalesce", ["to-number", ["get", "heat_intensity"]], 0.1],
            0.1,
            9,
            1,
            18,
          ],
          "circle-color": "rgba(0,0,0,0)",
          "circle-stroke-color": "#00E5FF",
          "circle-stroke-width": 2.2,
          "circle-opacity": 0.95,
        },
        filter: ["==", ["get", "event_id"], selectedEventId ?? "__none__"],
      });
    } else {
      map.setFilter(EVENT_SELECTED_LAYER_ID, ["==", ["get", "event_id"], selectedEventId ?? "__none__"]);
    }

    if (!map.getLayer(STATION_LAYER_ID)) {
      map.addLayer({
        id: STATION_LAYER_ID,
        type: "circle",
        source: STATION_SOURCE_ID,
        layout: { visibility: showOverlays ? "visible" : "none" },
        paint: {
          "circle-radius": 5,
          "circle-color": "#00E5FF",
          "circle-stroke-width": 1.2,
          "circle-stroke-color": "#CFD6EA",
          "circle-opacity": 0.9,
        },
      });
    } else {
      map.setLayoutProperty(STATION_LAYER_ID, "visibility", showOverlays ? "visible" : "none");
    }

    if (!map.getLayer(PROJECT_LAYER_ID)) {
      map.addLayer({
        id: PROJECT_LAYER_ID,
        type: "circle",
        source: PROJECT_SOURCE_ID,
        layout: { visibility: showOverlays ? "visible" : "none" },
        paint: {
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["coalesce", ["to-number", ["get", "magnitude"]], 0],
            0,
            5,
            25_000_000,
            8,
            150_000_000,
            13,
          ],
          "circle-color": "#423629",
          "circle-stroke-color": "#CFD6EA",
          "circle-stroke-width": 1.2,
          "circle-opacity": 0.85,
        },
      });
    } else {
      map.setLayoutProperty(PROJECT_LAYER_ID, "visibility", showOverlays ? "visible" : "none");
    }

    if (!map.getLayer(CORRIDOR_HEAT_LAYER_ID)) {
      map.addLayer({
        id: CORRIDOR_HEAT_LAYER_ID,
        type: "heatmap",
        source: CORRIDOR_SOURCE_ID,
        maxzoom: 13,
        layout: { visibility: showOverlays ? "visible" : "none" },
        paint: {
          "heatmap-weight": [
            "interpolate",
            ["linear"],
            ["coalesce", ["to-number", ["get", "magnitude"]], 1],
            0.5,
            0.2,
            3,
            1,
          ],
          "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 6, 0.5, 12, 1],
          "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 6, 10, 12, 34],
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0,
            "rgba(10,10,10,0)",
            0.4,
            "rgba(79,93,47,0.25)",
            1,
            "rgba(79,93,47,0.55)",
          ],
          "heatmap-opacity": 0.45,
        },
      });
    } else {
      map.setLayoutProperty(CORRIDOR_HEAT_LAYER_ID, "visibility", showOverlays ? "visible" : "none");
    }

    if (!map.getLayer(CORRIDOR_POINT_LAYER_ID)) {
      map.addLayer({
        id: CORRIDOR_POINT_LAYER_ID,
        type: "circle",
        source: CORRIDOR_SOURCE_ID,
        layout: { visibility: showOverlays ? "visible" : "none" },
        paint: {
          "circle-radius": 4,
          "circle-color": "#0A0A0A",
          "circle-stroke-color": "#4F5D2F",
          "circle-stroke-width": 1.8,
          "circle-opacity": 0.95,
        },
      });
    } else {
      map.setLayoutProperty(CORRIDOR_POINT_LAYER_ID, "visibility", showOverlays ? "visible" : "none");
    }

  }, [events, stations, capitalProjects, zoningCorridors, selectedEventId, showOverlays, mapReady]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) {
      return;
    }

    const showEventPopup = (feature: mapboxgl.MapboxGeoJSONFeature, lngLat: mapboxgl.LngLat) => {
      const props = feature.properties ?? {};
      const name = readText(props.name, "Event");
      const venue = readText(props.venue, "Unknown venue");
      const attendance = readNumber(props.adjusted_attendance);
      const heatIntensity = readNumber(props.heat_intensity);
      const confidence = readNumber(props.confidence);
      popupRef.current
        ?.setLngLat(lngLat)
        .setHTML(
          `<div><strong>${name}</strong><br/>Venue: ${venue}<br/>Attendance: ${attendance.toLocaleString()}<br/>Heat intensity: ${heatIntensity.toFixed(2)}<br/>Forecast confidence: ${(confidence * 100).toFixed(0)}%</div>`,
        )
        .addTo(map);
    };

    const showOverlayPopup = (
      feature: mapboxgl.MapboxGeoJSONFeature,
      lngLat: mapboxgl.LngLat,
      title: string,
      metricLabel: string,
    ) => {
      const props = feature.properties ?? {};
      const label = readText(props.label, title);
      const detail = readText(props.detail, "N/A");
      const magnitude = readNumber(props.magnitude);
      popupRef.current
        ?.setLngLat(lngLat)
        .setHTML(
          `<div><strong>${title}: ${label}</strong><br/>Detail: ${detail}<br/>${metricLabel}: ${magnitude.toLocaleString()}</div>`,
        )
        .addTo(map);
    };

    const onEventClick = (event: mapboxgl.MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (!feature?.properties) {
        return;
      }
      const eventId = readText(feature.properties.event_id, "");
      if (eventId) {
        onSelectEvent(eventId);
      }
    };
    const onEventEnter = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const onEventLeave = () => {
      map.getCanvas().style.cursor = "";
      popupRef.current?.remove();
    };
    const onEventMove = (event: mapboxgl.MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (feature) {
        showEventPopup(feature, event.lngLat);
      }
    };

    const onStationEnter = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const onStationLeave = () => {
      map.getCanvas().style.cursor = "";
      popupRef.current?.remove();
    };
    const onStationMove = (event: mapboxgl.MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (feature) {
        showOverlayPopup(feature, event.lngLat, "Station", "Node weight");
      }
    };

    const onProjectEnter = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const onProjectLeave = () => {
      map.getCanvas().style.cursor = "";
      popupRef.current?.remove();
    };
    const onProjectMove = (event: mapboxgl.MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (feature) {
        showOverlayPopup(feature, event.lngLat, "Capital project", "Budget (USD)");
      }
    };

    const onCorridorEnter = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const onCorridorLeave = () => {
      map.getCanvas().style.cursor = "";
      popupRef.current?.remove();
    };
    const onCorridorMove = (event: mapboxgl.MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (feature) {
        showOverlayPopup(feature, event.lngLat, "Zoning corridor", "Density multiplier");
      }
    };

    map.on("click", EVENT_POINT_LAYER_ID, onEventClick);
    map.on("mouseenter", EVENT_POINT_LAYER_ID, onEventEnter);
    map.on("mouseleave", EVENT_POINT_LAYER_ID, onEventLeave);
    map.on("mousemove", EVENT_POINT_LAYER_ID, onEventMove);
    map.on("mouseenter", STATION_LAYER_ID, onStationEnter);
    map.on("mouseleave", STATION_LAYER_ID, onStationLeave);
    map.on("mousemove", STATION_LAYER_ID, onStationMove);
    map.on("mouseenter", PROJECT_LAYER_ID, onProjectEnter);
    map.on("mouseleave", PROJECT_LAYER_ID, onProjectLeave);
    map.on("mousemove", PROJECT_LAYER_ID, onProjectMove);
    map.on("mouseenter", CORRIDOR_POINT_LAYER_ID, onCorridorEnter);
    map.on("mouseleave", CORRIDOR_POINT_LAYER_ID, onCorridorLeave);
    map.on("mousemove", CORRIDOR_POINT_LAYER_ID, onCorridorMove);

    return () => {
      map.off("click", EVENT_POINT_LAYER_ID, onEventClick);
      map.off("mouseenter", EVENT_POINT_LAYER_ID, onEventEnter);
      map.off("mouseleave", EVENT_POINT_LAYER_ID, onEventLeave);
      map.off("mousemove", EVENT_POINT_LAYER_ID, onEventMove);
      map.off("mouseenter", STATION_LAYER_ID, onStationEnter);
      map.off("mouseleave", STATION_LAYER_ID, onStationLeave);
      map.off("mousemove", STATION_LAYER_ID, onStationMove);
      map.off("mouseenter", PROJECT_LAYER_ID, onProjectEnter);
      map.off("mouseleave", PROJECT_LAYER_ID, onProjectLeave);
      map.off("mousemove", PROJECT_LAYER_ID, onProjectMove);
      map.off("mouseenter", CORRIDOR_POINT_LAYER_ID, onCorridorEnter);
      map.off("mouseleave", CORRIDOR_POINT_LAYER_ID, onCorridorLeave);
      map.off("mousemove", CORRIDOR_POINT_LAYER_ID, onCorridorMove);
    };
  }, [mapReady, onSelectEvent]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) {
      return;
    }
    if (map.getLayer(EVENT_SELECTED_LAYER_ID)) {
      map.setFilter(EVENT_SELECTED_LAYER_ID, ["==", ["get", "event_id"], selectedEventId ?? "__none__"]);
    }
  }, [selectedEventId, mapReady]);

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
        <div className="absolute inset-0 h-full w-full" ref={mapContainerRef} />
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
        {mapError ? (
          <div className="absolute top-12 left-3 rounded bg-red-900/40 px-3 py-1 text-[11px] font-mono text-red-100">
            {mapError}
          </div>
        ) : null}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-3 text-[11px] font-mono text-white/55">
        <span>Events: weighted heatmap + intensity nodes (hover for live metrics)</span>
        <span>•</span>
        <span>Blue: transit stations</span>
        <span>•</span>
        <span>Taupe: capital budget points</span>
        <span>•</span>
        <span>Olive: zoning corridor density layer</span>
      </div>
    </section>
  );
}
