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
    <section className="card">
      <div className="card-header">
        <h2>Weather Pressure Test</h2>
        <span className="badge">{temperatureF.toFixed(0)} F</span>
      </div>
      <input
        aria-label="Temperature slider"
        className="slider"
        disabled={disabled}
        max={110}
        min={50}
        onChange={(event) => onTemperatureChange(Number(event.target.value))}
        type="range"
        value={temperatureF}
      />
      <div className="row">
        <span className="muted">50 F</span>
        <button className="button" disabled={disabled} onClick={onWorstCase} type="button">
          Worst Case (102 F)
        </button>
        <span className="muted">110 F</span>
      </div>
    </section>
  );
}
