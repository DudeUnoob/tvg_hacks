import type { DispatchRecommendation } from "../types/api";

interface DispatchPanelProps {
  recommendations: DispatchRecommendation[];
  selectedEventId: string | null;
}

export function DispatchPanel({ recommendations, selectedEventId }: DispatchPanelProps) {
  const visible = selectedEventId
    ? recommendations.filter((item) => item.event_id === selectedEventId)
    : recommendations;

  return (
    <section className="panel-hardware rounded-xl border border-white/10 p-5">
      <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-4">
        <h2 className="font-mono text-sm tracking-widest text-[#00E5FF]">Layer 4: Dispatch Recommendations</h2>
        <span className="font-mono text-xs text-white/50">{visible.length} item(s)</span>
      </div>
      {visible.length === 0 ? (
        <p className="text-sm text-white/55">No dispatch recommendations available for the current selection.</p>
      ) : (
        visible.map((recommendation) => (
          <article
            className="rounded-lg border border-white/10 bg-black/30 p-4 mb-4 last:mb-0"
            key={recommendation.event_id}
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <h3 className="text-base font-semibold text-white">{recommendation.event_name}</h3>
              <span className="text-xs font-mono text-[#00E5FF] whitespace-nowrap">
                {(recommendation.confidence * 100).toFixed(1)}% conf
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3 text-sm text-white/70">
              <div>Pre-charge start: {new Date(recommendation.precharge_start_time).toLocaleString()}</div>
              <div>Lead time: {recommendation.lead_time_hours}h</div>
              <div>Temp: {recommendation.temperature_f.toFixed(1)} F</div>
              <div>Wx multiplier: {recommendation.weather_multiplier.toFixed(2)}</div>
              <div>Revenue est: ${recommendation.revenue_estimate_usd.toLocaleString()}</div>
            </div>
            <p className="text-xs text-white/65 mb-3">{recommendation.comparable_signal}</p>
            <div className="rounded border border-white/8 bg-black/20 px-3 py-2 mb-3 text-xs text-white/70">
              Energy profile: {recommendation.energy_profile.source} · matched{" "}
              {recommendation.energy_profile.matched_venue ?? "fallback"} · venue factor{" "}
              {recommendation.energy_profile.venue_intensity_factor.toFixed(3)}
            </div>
            <ul className="space-y-2 text-sm mb-3">
              {recommendation.targets.map((target) => (
                <li
                  className="rounded border border-white/8 bg-black/25 px-3 py-2"
                  key={`${recommendation.event_id}-${target.zip_code}`}
                >
                  #{target.rank} ZIP {target.zip_code} · {(target.recommended_capacity_pct * 100).toFixed(0)}%
                  pre-charge · +{target.projected_load_delta_mw.toFixed(3)} MW · {target.estimated_battery_count} batteries
                </li>
              ))}
            </ul>
            <p className="text-xs text-white/70">{recommendation.reasoning_trace}</p>
          </article>
        ))
      )}
    </section>
  );
}
