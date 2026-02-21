export interface ErcotSnapshot {
  price_mwh: number;
  load_mw: number;
  source: string;
  updated_at: string;
}

export interface EventResponse {
  event_id: string;
  name: string;
  source: string;
  venue: string;
  start_time: string;
  end_time: string;
  baseline_attendance: number;
  latitude: number;
  longitude: number;
  radius_meters: number;
  projected_dispersal_peak: string;
  projected_dispersal_end: string;
  parking_infrastructure_score: number;
  transit_access_score: number;
}

export interface EventListResponse {
  events: EventResponse[];
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
  weather_multiplier: number;
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

export interface CrowdSignalResponse {
  event_id: string;
  observed_at: string;
  camera_count: number;
  avg_parking_fill_pct: number;
  estimated_attendance: number;
  confidence: number;
  fallback_used: boolean;
  reasoning: string;
}

export interface ZipLoadProjection {
  zip_code: string;
  projected_load_delta_mw: number;
  share_of_wave_pct: number;
  peak_time: string;
}

export interface EnergyProfile {
  requested_venue: string;
  matched_venue: string | null;
  source: string;
  temperature_f: number;
  lower_bin_f: number | null;
  upper_bin_f: number | null;
  interpolated_kwh: number | null;
  base_kwh: number | null;
  weather_multiplier: number;
  venue_intensity_factor: number;
}

export interface WeatherSimulationResponse {
  event_id: string;
  temperature_f: number;
  weather_multiplier: number;
  energy_profile: EnergyProfile;
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
  weather_multiplier: number;
  revenue_estimate_usd: number;
  comparable_signal: string;
  reasoning_trace: string;
  energy_profile: EnergyProfile;
  targets: DispatchTarget[];
}

export interface ActiveDispatchResponse {
  recommendations: DispatchRecommendation[];
}

export interface EventSyncResponse {
  ingested_count: number;
  events: EventResponse[];
  force: boolean;
}

export interface DispatchResponse {
  recommendation: DispatchRecommendation;
}
