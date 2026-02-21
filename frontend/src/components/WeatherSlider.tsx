interface WeatherSliderProps {
  temperatureF: number;
  onTemperatureChange: (temperatureF: number) => void;
  onWorstCase: () => void;
  disabled?: boolean;
}

export function WeatherSlider({
  temperatureF,
  onTemperatureChange,
  onWorstCase,
  disabled = false,
}: WeatherSliderProps) {
  return (
    <section className="panel-hardware rounded-xl border border-white/10 p-5">
      <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-4">
        <h2 className="font-mono text-sm tracking-widest text-[#00E5FF]">Weather Pressure Test</h2>
        <span className="rounded-full border border-white/20 bg-black/40 px-3 py-1 font-mono text-xs">
          {temperatureF.toFixed(0)} F
        </span>
      </div>
      <input
        aria-label="Temperature slider"
        className="w-full accent-[#FF5A7A]"
        disabled={disabled}
        max={110}
        min={50}
        onChange={(event) => onTemperatureChange(Number(event.target.value))}
        type="range"
        value={temperatureF}
      />
      <div className="mt-3 flex items-center justify-between gap-3">
        <span className="font-mono text-xs text-white/55">50 F</span>
        <button
          className="rounded border border-[#FF5A7A]/70 px-3 py-1.5 text-xs font-mono text-[#FF5A7A] hover:bg-[#FF5A7A]/15 disabled:opacity-50"
          disabled={disabled}
          onClick={onWorstCase}
          type="button"
        >
          Worst Case (102 F)
        </button>
        <span className="font-mono text-xs text-white/55">110 F</span>
      </div>
    </section>
  );
}
