import { ThermometerSun } from "lucide-react";

interface WeatherStressProps {
  temperatureF: number;
  onTemperatureChange: (temperatureF: number) => void;
  onWorstCase: () => void;
  projectedPeakMw: number | null;
  weatherMultiplier: number | null;
  loading?: boolean;
  disabled?: boolean;
  error?: string | null;
}

export function WeatherStress({
  temperatureF,
  onTemperatureChange,
  onWorstCase,
  projectedPeakMw,
  weatherMultiplier,
  loading = false,
  disabled = false,
  error = null,
}: WeatherStressProps) {
  const stressPercent = Math.max(0, Math.min(100, ((temperatureF - 50) / 60) * 100));
  const fallbackPeak = Math.max(0, (temperatureF - 65) * 6.2);
  const visiblePeak = projectedPeakMw ?? fallbackPeak;

  return (
    <div className="tech-panel tech-interactive p-6 flex flex-col h-full min-h-[420px]">
      <div className="flex items-center justify-between mb-6 border-b border-white/10 pb-4">
        <h2 className="text-xl uppercase tracking-widest text-pale-slate flex items-center gap-2">
          <ThermometerSun className="text-lavender w-5 h-5" />
          Layer 3: Simulation
        </h2>
        <span className="telemetry-text text-grey-olive">{loading ? "RUNNING..." : "STRESS TEST"}</span>
      </div>

      <div className="flex-1 flex flex-col justify-between">
        <div className="space-y-4">
          <div className="flex justify-between items-end">
            <span className="font-mono text-xs text-grey-olive uppercase tracking-widest">Ambient Context</span>
            <span className="font-space text-4xl font-bold text-white tracking-tighter">
              {temperatureF}°<span className="text-xl text-pale-slate">F</span>
            </span>
          </div>

          <div className="relative pt-4">
            <input
              aria-label="Temperature stress slider"
              className="w-full h-1 bg-white/10 rounded-full appearance-none outline-none overflow-hidden accent-olive disabled:opacity-60"
              disabled={disabled}
              max={110}
              min={50}
              onChange={(event) => onTemperatureChange(Number(event.target.value))}
              style={{ boxShadow: "inset 0 0 5px rgba(0,0,0,0.5)" }}
              type="range"
              value={temperatureF}
            />
            <div
              className="absolute top-4 left-0 h-1 bg-olive rounded-full transition-all duration-75"
              style={{ width: `${((temperatureF - 50) / 60) * 100}%`, boxShadow: "0 0 10px rgba(79, 93, 47, 0.8)" }}
            />
          </div>
          <div className="flex justify-between items-center font-mono text-[10px] text-grey-olive mt-2">
            <span>50°F (Mild)</span>
            <button
              className="rounded border border-[#FF5A7A]/70 px-2 py-1 text-[10px] text-[#FF5A7A] hover:bg-[#FF5A7A]/15 disabled:opacity-50"
              disabled={disabled}
              onClick={onWorstCase}
              type="button"
            >
              Worst Case 102°F
            </button>
            <span>110°F (Critical)</span>
          </div>
          {weatherMultiplier !== null ? (
            <p className="font-mono text-[11px] text-pale-slate">Weather multiplier: {weatherMultiplier.toFixed(2)}x</p>
          ) : null}
          {error ? <p className="font-mono text-[11px] text-red-300">Simulation error: {error}</p> : null}
        </div>

        <div className="mt-8 space-y-2">
          <div className="flex justify-between items-center mb-4">
            <span className="font-mono text-xs text-grey-olive uppercase tracking-widest">Projected Load Strain</span>
            <span className={`font-mono text-sm font-bold ${stressPercent > 80 ? "text-taupe animate-pulse" : "text-olive"}`}>
              +{visiblePeak.toFixed(1)} MW
            </span>
          </div>

          <div className="flex gap-1 h-32 items-end">
            {[...Array(15)].map((_, index) => {
              const height = 20 + Math.pow(index, 1.8) * 0.5;
              const isActive = stressPercent > (index / 15) * 100;
              return (
                <div
                  className="flex-1 rounded-sm transition-all duration-150"
                  key={index}
                  style={{
                    height: `${height}%`,
                    backgroundColor: isActive ? (stressPercent > 80 ? "#423629" : "#4F5D2F") : "#1A1A1A",
                    boxShadow: isActive ? `0 0 8px ${stressPercent > 80 ? "#423629" : "#4F5D2F"}` : "none",
                    opacity: isActive ? 0.85 : 0.35,
                  }}
                />
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
