export interface ErcotSnapshot {
  price_mwh: number;
  load_mw: number;
  source: string;
  updated_at: string;
}

export interface MapEventState {
  event_id: string;
  name: string;
  venue: string;
  latitude: number;
  longitude: number;
  baseline_attendance: number;
  adjusted_attendance: number;
  confidence: number;
  projected_dispersal_peak: string;
  heat_intensity: number;
  wave_zip_codes: string[];
}

export interface MapStateResponse {
  as_of: string;
  ercot: ErcotSnapshot;
  events: MapEventState[];
}

export interface ForecastResponse {
  event_id: string;
  generated_at: string;
  baseline_attendance: number;
  vlm_estimated_attendance: number;
  confidence: number;
  adjusted_attendance: number;
  adjustment_delta: number;
  fallback_used: boolean;
  reasoning_trace: string;
}

export interface ZipLoadProjection {
  zip_code: string;
  projected_load_delta_mw: number;
  share_of_wave_pct: number;
  peak_time: string;
}

export interface WeatherSimulationResponse {
  event_id: string;
  temperature_f: number;
  weather_multiplier: number;
  projected_peak_mw: number;
  forecast: ForecastResponse;
  zip_projections: ZipLoadProjection[];
}

export interface UrbanStation {
  station_id: string;
  name: string;
  latitude: number;
  longitude: number;
  corridor: string;
}

export interface CapitalProject {
  project_id: string;
  name: string;
  latitude: number;
  longitude: number;
  status: string;
  estimated_budget_usd: number;
}

export interface ZoningCorridor {
  corridor_id: string;
  name: string;
  latitude: number;
  longitude: number;
  zoning_type: string;
  density_multiplier: number;
}

export interface UrbanOverlaysResponse {
  stations: UrbanStation[];
  capital_projects: CapitalProject[];
  zoning_corridors: ZoningCorridor[];
}

export interface UrbanSimulationResult {
  scenario_id: string;
  scenario_name: string;
  horizon_years: number;
  projected_load_mw: number;
  current_capacity_mw: number;
  transformer_headroom_mw: number;
  recommended_battery_count: number;
  grid_stress_level: string;
}

export interface UrbanSimulationResponse {
  simulation: UrbanSimulationResult;
}

export interface DispatchTarget {
  rank: number;
  zip_code: string;
  recommended_capacity_pct: number;
  projected_load_delta_mw: number;
  estimated_battery_count: number;
}

export interface DispatchRecommendation {
  event_id: string;
  event_name: string;
  generated_at: string;
  precharge_start_time: string;
  lead_time_hours: number;
  confidence: number;
  temperature_f: number;
  revenue_estimate_usd: number;
  comparable_signal: string;
  reasoning_trace: string;
  targets: DispatchTarget[];
}

export interface ActiveDispatchResponse {
  recommendations: DispatchRecommendation[];
}
