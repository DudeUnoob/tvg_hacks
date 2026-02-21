import { useEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
import { Terminal, Zap } from "lucide-react";

import type { DispatchRecommendation } from "../types/api";

interface DispatchTerminalProps {
  recommendation: DispatchRecommendation | null;
  loading?: boolean;
  error?: string | null;
}

function buildReasoningLines(recommendation: DispatchRecommendation | null): string[] {
  if (!recommendation) {
    return [
      "SYSTEM INITIATIVE: LAYER 4 ACTUATION",
      "> Awaiting active dispatch recommendation from backend.",
      "> Select an event node to generate a command payload.",
    ];
  }
  const topTargets = recommendation.targets.slice(0, 3).map((target) => target.zip_code).join(", ");
  const batteryTotal = recommendation.targets.reduce((total, target) => total + target.estimated_battery_count, 0);
  return [
    "SYSTEM INITIATIVE: LAYER 4 ACTUATION",
    `> ${recommendation.event_name} at ${(recommendation.confidence * 100).toFixed(1)}% confidence.`,
    `> Weather multiplier ${recommendation.weather_multiplier.toFixed(2)} at ${recommendation.temperature_f.toFixed(1)}F.`,
    `> Ranked target ZIPs: ${topTargets || "none"}.`,
    `> Projected arbitrage value: $${recommendation.revenue_estimate_usd.toLocaleString()}.`,
    `> Estimated fleet allocation: ${batteryTotal.toLocaleString()} batteries.`,
    `> ${recommendation.reasoning_trace}`,
  ];
}

function buildPayload(recommendation: DispatchRecommendation | null): string {
  if (!recommendation) {
    return JSON.stringify(
      {
        status: "awaiting_recommendation",
        trigger_event: null,
        target_zones: [],
      },
      null,
      2,
    );
  }

  const batteryTotal = recommendation.targets.reduce((total, target) => total + target.estimated_battery_count, 0);
  return JSON.stringify(
    {
      dispatch_id: `BP-${recommendation.event_id}-${recommendation.generated_at.slice(0, 19)}`,
      trigger_event: recommendation.event_id,
      event_name: recommendation.event_name,
      generated_at: recommendation.generated_at,
      precharge_start_time: recommendation.precharge_start_time,
      target_zones: recommendation.targets.map((target) => target.zip_code),
      target_capacities_pct: recommendation.targets.map((target) => ({
        zip_code: target.zip_code,
        recommended_capacity_pct: target.recommended_capacity_pct,
      })),
      weather_multiplier: recommendation.weather_multiplier,
      fleet_allocation: batteryTotal,
      expected_revenue_usd: recommendation.revenue_estimate_usd,
      authorization: "PENDING_OPERATOR",
    },
    null,
    2,
  );
}

export function DispatchTerminal({ recommendation, loading = false, error = null }: DispatchTerminalProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [typedJson, setTypedJson] = useState("");
  const [typingComplete, setTypingComplete] = useState(false);
  const reasoningLines = useMemo(() => buildReasoningLines(recommendation), [recommendation]);
  const jsonPayload = useMemo(() => buildPayload(recommendation), [recommendation]);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from(".reasoning-line", {
        opacity: 0,
        x: -18,
        duration: 0.45,
        stagger: 0.2,
        ease: "power2.out",
      });
    }, containerRef);
    return () => ctx.revert();
  }, [reasoningLines]);

  useEffect(() => {
    setTypedJson("");
    setTypingComplete(false);
    let currentIndex = 0;
    const intervalId = window.setInterval(() => {
      if (currentIndex <= jsonPayload.length) {
        setTypedJson(jsonPayload.slice(0, currentIndex));
        currentIndex += 3;
      } else {
        window.clearInterval(intervalId);
        setTypingComplete(true);
      }
    }, 12);
    return () => window.clearInterval(intervalId);
  }, [jsonPayload]);

  return (
    <section className="max-w-[1440px] mx-auto px-6 mb-24" ref={containerRef}>
      <div className="tech-panel border-white/20 p-8">
        <div className="flex items-center gap-3 mb-8 border-b border-white/10 pb-4">
          <Terminal className="text-olive w-6 h-6" />
          <h2 className="text-2xl font-space uppercase tracking-widest text-white">Layer 4: Actuation Engine</h2>
          <span className="ml-auto font-mono text-xs text-grey-olive tracking-widest border border-white/10 px-3 py-1 rounded-sm">
            TERMINAL // SECURE
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <div className="font-mono text-sm leading-relaxed space-y-4">
            {reasoningLines.map((line, index) => (
              <p className={`reasoning-line ${index === 0 ? "text-olive font-bold" : "text-pale-slate"}`} key={line}>
                {line}
              </p>
            ))}
            {error ? <p className="reasoning-line text-red-300">Error: {error}</p> : null}
            {loading ? <p className="reasoning-line text-grey-olive animate-pulse">Streaming backend recommendations...</p> : null}
            <p className="reasoning-line text-taupe animate-pulse mt-8">_</p>
          </div>

          <div className="flex flex-col h-full">
            <div className="flex-1 bg-black/50 border border-white/5 p-4 rounded-sm font-mono text-xs text-grey-olive relative overflow-hidden">
              <div className="absolute top-0 right-0 p-2 text-[10px] text-taupe border-b border-l border-white/5 bg-dark-panel">
                payload.json
              </div>
              <pre className="whitespace-pre-wrap mt-4 text-lavender">
                {typedJson}
                {typingComplete ? "" : <span className="animate-pulse bg-lavender w-2 h-4 inline-block align-middle ml-1" />}
              </pre>
            </div>

            <button
              className={`mt-6 w-full py-4 rounded-sm font-space font-bold text-lg tracking-widest transition-all duration-300 flex items-center justify-center gap-3 ${
                typingComplete && !loading
                  ? "bg-olive text-white shadow-[0_0_20px_rgba(79,93,47,0.4)] hover:shadow-[0_0_30px_rgba(79,93,47,0.8)] hover:bg-[#5a6a36] cursor-pointer"
                  : "bg-dark-panel border border-white/5 text-grey-olive cursor-not-allowed opacity-50"
              }`}
              disabled={!typingComplete || loading}
              type="button"
            >
              <Zap className={`w-5 h-5 ${typingComplete && !loading ? "text-white" : "text-grey-olive"}`} />
              [ EXECUTE DISPATCH ]
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
