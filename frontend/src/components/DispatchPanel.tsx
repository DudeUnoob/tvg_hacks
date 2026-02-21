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
    <section className="card dispatch-panel">
      <div className="card-header">
        <h2>Layer 4 Dispatch Recommendations</h2>
        <span className="muted">{visible.length} items</span>
      </div>
      {visible.length === 0 ? (
        <p className="muted">No dispatch recommendations yet.</p>
      ) : (
        visible.map((recommendation) => (
          <article className="dispatch-item" key={recommendation.event_id}>
            <h3>{recommendation.event_name}</h3>
            <p className="muted">
              Start precharge: {new Date(recommendation.precharge_start_time).toLocaleString()}
            </p>
            <p className="muted">
              Revenue estimate: ${recommendation.revenue_estimate_usd.toLocaleString()}
            </p>
            <ul>
              {recommendation.targets.map((target) => (
                <li key={`${recommendation.event_id}-${target.zip_code}`}>
                  #{target.rank} zip {target.zip_code} @ {(target.recommended_capacity_pct * 100).toFixed(0)}%
                  capacity ({target.estimated_battery_count} batteries)
                </li>
              ))}
            </ul>
            <p>{recommendation.reasoning_trace}</p>
          </article>
        ))
      )}
    </section>
  );
}
