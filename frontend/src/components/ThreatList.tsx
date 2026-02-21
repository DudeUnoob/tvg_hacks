import { useEffect, useMemo, useRef } from "react";
import gsap from "gsap";
import { AlertTriangle, MapPin, Users } from "lucide-react";

import type { EventResponse, MapEventState } from "../types/api";

interface ThreatListProps {
  events: MapEventState[];
  eventMetadataById: Record<string, EventResponse>;
  selectedEventId: string | null;
  onSelectEvent: (eventId: string) => void;
  loading?: boolean;
}

function toClock(value: string | undefined): string {
  if (!value) {
    return "--:--";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--:--";
  }
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function ThreatList({
  events,
  eventMetadataById,
  selectedEventId,
  onSelectEvent,
  loading = false,
}: ThreatListProps) {
  const pathRef = useRef<SVGPathElement>(null);
  const visibleEvents = useMemo(
    () => [...events].sort((left, right) => right.adjusted_attendance - left.adjusted_attendance).slice(0, 3),
    [events],
  );

  const activeIndex = useMemo(() => {
    if (!visibleEvents.length) {
      return 0;
    }
    if (!selectedEventId) {
      return 0;
    }
    const index = visibleEvents.findIndex((event) => event.event_id === selectedEventId);
    return index >= 0 ? index : 0;
  }, [selectedEventId, visibleEvents]);

  useEffect(() => {
    if (!pathRef.current) {
      return;
    }
    const length = pathRef.current.getTotalLength();
    gsap.set(pathRef.current, { strokeDasharray: length, strokeDashoffset: length });
    gsap.to(pathRef.current, { strokeDashoffset: 0, duration: 1.2, ease: "power2.out" });
  }, [activeIndex]);

  return (
    <div className="tech-panel tech-interactive p-6 flex flex-col h-full min-h-[420px]">
      <div className="flex items-center justify-between mb-6 border-b border-white/10 pb-4">
        <h2 className="text-xl uppercase tracking-widest text-pale-slate flex items-center gap-2">
          <AlertTriangle className="text-olive w-5 h-5" />
          Layer 1: Intelligence
        </h2>
        <span className="telemetry-text text-taupe animate-pulse">
          {loading ? "SYNCING..." : "LIVELINK ACTIVE"}
        </span>
      </div>

      <div className="flex-1 flex flex-col gap-4 overflow-hidden relative">
        {!visibleEvents.length ? (
          <div className="h-full rounded-sm border border-white/10 bg-black/25 p-4 text-sm text-grey-olive">
            No active events yet. Trigger live sync and keep this panel open for new threats.
          </div>
        ) : (
          visibleEvents.map((event, idx) => {
            const metadata = eventMetadataById[event.event_id];
            const isActive = idx === activeIndex;
            return (
              <button
                className={`w-full text-left p-4 border rounded-sm transition-all duration-500 ${
                  isActive
                    ? "bg-olive/10 border-olive/50 scale-[1.02]"
                    : "bg-dark-panel border-white/5 opacity-65 hover:opacity-100"
                }`}
                key={event.event_id}
                onClick={() => onSelectEvent(event.event_id)}
                type="button"
              >
                <div className="flex justify-between items-start mb-2 gap-3">
                  <h3 className={`font-space font-semibold tracking-wide ${isActive ? "text-white" : "text-pale-slate"}`}>
                    {event.name}
                  </h3>
                  <span className={`telemetry-text whitespace-nowrap ${isActive ? "text-olive" : "text-grey-olive"}`}>
                    T - {toClock(event.projected_dispersal_peak)}
                  </span>
                </div>
                <div className="flex flex-wrap gap-4 text-xs font-mono text-grey-olive mt-3">
                  <span className="flex items-center gap-1">
                    <Users className="w-3 h-3" /> {event.adjusted_attendance.toLocaleString()} est
                  </span>
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3 h-3" /> {metadata?.venue ?? event.venue}
                  </span>
                </div>
              </button>
            );
          })
        )}
      </div>

      <div className="mt-6 pt-4 border-t border-white/10">
        <div className="flex justify-between mb-2">
          <span className="telemetry-text text-[10px] text-grey-olive">Projected Dispersal Sequence</span>
          <span className="telemetry-text text-[10px] text-olive">T+0..T+4h</span>
        </div>
        <svg viewBox="0 0 100 40" className="w-full h-16 overflow-visible" preserveAspectRatio="none">
          <line x1="0" y1="20" x2="100" y2="20" stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />
          <line x1="0" y1="40" x2="100" y2="40" stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />
          <path
            ref={pathRef}
            className="drop-shadow-[0_0_8px_rgba(79,93,47,0.8)]"
            d={
              activeIndex === 0
                ? "M 0 35 Q 20 35, 40 10 T 80 5 T 100 30"
                : activeIndex === 1
                  ? "M 0 30 Q 30 30, 50 5 T 90 20 T 100 35"
                  : "M 0 38 Q 10 38, 30 15 T 70 8 T 100 30"
            }
            fill="none"
            stroke="#4F5D2F"
            strokeLinecap="round"
            strokeWidth="2"
          />
        </svg>
      </div>
    </div>
  );
}
