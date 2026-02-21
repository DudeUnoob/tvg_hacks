interface UrbanOverlayToggleProps {
  showOverlays: boolean;
  stationCount: number;
  projectCount: number;
  zoningCount: number;
  onToggleOverlays: (enabled: boolean) => void;
  onRunFiveYear: () => void;
  onRunTenYear: () => void;
  simulationSummary: string;
}

export function UrbanOverlayToggle({
  showOverlays,
  stationCount,
  projectCount,
  zoningCount,
  onToggleOverlays,
  onRunFiveYear,
  onRunTenYear,
  simulationSummary,
}: UrbanOverlayToggleProps) {
  return (
    <section className="panel-hardware rounded-xl border border-white/10 p-5">
      <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-4">
        <h2 className="font-mono text-sm tracking-widest text-[#00E5FF]">Urban Planning Mode</h2>
        <label className="inline-flex items-center gap-2 text-xs font-mono text-white/70">
          <input
            checked={showOverlays}
            onChange={(event) => onToggleOverlays(event.target.checked)}
            type="checkbox"
          />
          <span>Show overlays</span>
        </label>
      </div>
      <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono mb-4">
        <div className="rounded border border-white/10 bg-black/30 px-2 py-2">Stations: {stationCount}</div>
        <div className="rounded border border-white/10 bg-black/30 px-2 py-2">Projects: {projectCount}</div>
        <div className="rounded border border-white/10 bg-black/30 px-2 py-2">Zoning: {zoningCount}</div>
      </div>
      <div className="flex items-center gap-2 mb-3">
        <button
          className="rounded border border-[#00E5FF]/70 px-3 py-1.5 text-xs font-mono text-[#00E5FF] hover:bg-[#00E5FF]/15"
          onClick={onRunFiveYear}
          type="button"
        >
          Simulate 5 years
        </button>
        <button
          className="rounded border border-[#00E5FF]/70 px-3 py-1.5 text-xs font-mono text-[#00E5FF] hover:bg-[#00E5FF]/15"
          onClick={onRunTenYear}
          type="button"
        >
          Simulate 10 years
        </button>
      </div>
      <p className="text-sm text-white/70">{simulationSummary}</p>
    </section>
  );
}
