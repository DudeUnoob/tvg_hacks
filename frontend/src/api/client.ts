import type {
  ActiveDispatchResponse,
  CrowdSignalResponse,
  DispatchResponse,
  EventListResponse,
  DispatchRecommendation,
  EventSyncResponse,
  ForecastResponse,
  MapStateResponse,
  UrbanOverlaysResponse,
  UrbanSimulationResponse,
  WeatherSimulationResponse,
} from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers ?? {});
  if (!headers.has("Content-Type") && init?.body) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers,
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

export async function fetchEvents(): Promise<EventListResponse["events"]> {
  const response = await request<EventListResponse>("/events");
  return response.events;
}

export async function fetchActiveEvents(at?: string): Promise<EventListResponse["events"]> {
  const query = at ? `?at=${encodeURIComponent(at)}` : "";
  const response = await request<EventListResponse>(`/events/active${query}`);
  return response.events;
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

export async function fetchDispatchForEvent(eventId: string): Promise<DispatchRecommendation> {
  const response = await request<DispatchResponse>(`/layer4/dispatch/${eventId}`);
  return response.recommendation;
}

export function confirmCrowd(
  eventId: string,
  payload?: { sample_size?: number; camera_ids?: string[] },
): Promise<CrowdSignalResponse> {
  return request<CrowdSignalResponse>(`/crowd/confirm/${eventId}`, {
    method: "POST",
    body: JSON.stringify(payload ?? { sample_size: 4 }),
  });
}

export function fetchForecast(eventId: string, refresh = false): Promise<ForecastResponse> {
  return request<ForecastResponse>(`/forecasts/${eventId}?refresh=${String(refresh)}`);
}

export function syncLiveEvents(force = false): Promise<EventSyncResponse> {
  return request<EventSyncResponse>(`/events/sync-live?force=${String(force)}`, {
    method: "POST",
  });
}
