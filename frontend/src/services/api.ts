import axios from 'axios';
import type {

  VehicleDetail,
  VehicleSummary,
  SessionCreatePayload,
  SessionResponsePayload,
  SessionUpdatePayload,
  AnalyticsSummaryPayload,
} from '@shared/types/tco.types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api/v1',
  timeout: 10000,
});

export const fetchVehicles = async () => {
  const { data } = await api.get<VehicleSummary[]>('/vehicles');
  return data;
};

export const fetchVehicle = async (vehicleId: string) => {
  const { data } = await api.get<VehicleDetail>(`/vehicles/${vehicleId}`);
  return data;
};



export const createSession = async (payload: SessionCreatePayload) => {
  const { data } = await api.post<SessionResponsePayload>('/sessions', payload);
  return data;
};

export const updateSession = async (
  sessionId: string,
  payload: SessionUpdatePayload,
  signal?: AbortSignal
) => {
  const { data } = await api.put<SessionResponsePayload>(`/sessions/${sessionId}`, payload, {
    signal,
  });
  return data;
};

export const fetchSession = async (sessionId: string) => {
  const { data } = await api.get<SessionResponsePayload>(`/sessions/${sessionId}`);
  return data;
};

export const fetchAnalyticsSummary = async () => {
  const { data } = await api.get<AnalyticsSummaryPayload>('/analytics/summary');
  return data;
};
