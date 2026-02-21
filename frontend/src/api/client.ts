import type {
  ActiveDispatchResponse,
  DispatchRecommendation,
  MapStateResponse,
  UrbanOverlaysResponse,
  UrbanSimulationResponse,
  WeatherSimulationResponse,
} from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Request failed (${response.status}): ${text}`);
  }
  return (await response.json()) as T;
}

export function fetchMapState(): Promise<MapStateResponse> {
  return request<MapStateResponse>("/layer3/map-state");
}

export function simulateWeather(
  eventId: string,
  temperatureF: number,
): Promise<WeatherSimulationResponse> {
  return request<WeatherSimulationResponse>("/layer3/simulate", {
    method: "POST",
    body: JSON.stringify({ event_id: eventId, temperature_f: temperatureF }),
  });
}

export function fetchUrbanOverlays(): Promise<UrbanOverlaysResponse> {
  return request<UrbanOverlaysResponse>("/layer3/urban-overlays");
}

export function simulateUrbanImpact(payload: {
  project_id?: string;
  project_name?: string;
  horizon_years: number;
  building_units?: number;
  commercial_sqft?: number;
}): Promise<UrbanSimulationResponse> {
  return request<UrbanSimulationResponse>("/layer3/urban-simulate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchActiveDispatch(): Promise<DispatchRecommendation[]> {
  const response = await request<ActiveDispatchResponse>("/layer4/dispatch/active");
  return response.recommendations;
}
