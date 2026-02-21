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
    <section className="card">
      <div className="card-header">
        <h2>Urban Planning Mode</h2>
        <label className="switch">
          <input
            checked={showOverlays}
            onChange={(event) => onToggleOverlays(event.target.checked)}
            type="checkbox"
          />
          <span>Show overlays</span>
        </label>
      </div>
      <div className="overlay-stats">
        <div>Stations: {stationCount}</div>
        <div>Capital projects: {projectCount}</div>
        <div>Zoning corridors: {zoningCount}</div>
      </div>
      <div className="row">
        <button className="button" onClick={onRunFiveYear} type="button">
          Simulate 5 years
        </button>
        <button className="button" onClick={onRunTenYear} type="button">
          Simulate 10 years
        </button>
      </div>
      <p className="muted">{simulationSummary}</p>
    </section>
  );
}
