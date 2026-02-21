import type { MapEventState } from "../types/api";

interface MapCanvasProps {
  events: MapEventState[];
  selectedEventId: string | null;
  onSelectEvent: (eventId: string) => void;
}

const bounds = {
  minLat: 30.15,
  maxLat: 30.42,
  minLon: -97.9,
  maxLon: -97.6,
};

function projectToCanvas(latitude: number, longitude: number): { x: number; y: number } {
  const x = ((longitude - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * 100;
  const y = (1 - (latitude - bounds.minLat) / (bounds.maxLat - bounds.minLat)) * 100;
  return { x, y };
}

export function MapCanvas({ events, selectedEventId, onSelectEvent }: MapCanvasProps) {
  return (
    <section className="card">
      <div className="card-header">
        <h2>Layer 3 Real-Time Canvas</h2>
        <span className="muted">{events.length} events</span>
      </div>
      <div className="map-canvas">
        {events.length === 0 ? (
          <div className="empty-state">
            No events available yet. Ingest events in backend first, then refresh this page.
          </div>
        ) : null}
        {events.map((event) => {
          const { x, y } = projectToCanvas(event.latitude, event.longitude);
          const size = 12 + event.heat_intensity * 30;
          const selected = selectedEventId === event.event_id;
          return (
            <button
              key={event.event_id}
              className={`event-node${selected ? " selected" : ""}`}
              style={{
                left: `${x}%`,
                top: `${y}%`,
                width: `${size}px`,
                height: `${size}px`,
              }}
              onClick={() => onSelectEvent(event.event_id)}
              title={`${event.name} (${event.adjusted_attendance.toLocaleString()} people)`}
              type="button"
            />
          );
        })}
      </div>
      <div className="legend">
        <span>Node size = crowd heat intensity proxy</span>
        <span>Click node to drive weather + dispatch panels</span>
      </div>
    </section>
  );
}
