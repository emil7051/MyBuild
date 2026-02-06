import axios from 'axios';
import type {
  SessionCreatePayload,
  SessionCreateResponsePayload,
  SessionResponsePayload,
  SessionUpdatePayload,
} from '@shared/types/tco.types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api/v1',
  timeout: 10000,
  withCredentials: true,
});

type SessionRequestOptions = {
  signal?: AbortSignal;
};

const getSessionConfig = (options: SessionRequestOptions = {}) => {
  const config: { signal?: AbortSignal } = {};
  if (options.signal) {
    config.signal = options.signal;
  }
  return config;
};

export const createSession = async (payload: SessionCreatePayload) => {
  const { data } = await api.post<SessionCreateResponsePayload>('/sessions', payload);
  return data;
};

export const updateSession = async (
  sessionId: string,
  payload: SessionUpdatePayload,
  options: SessionRequestOptions = {}
) => {
  const { data } = await api.put<SessionResponsePayload>(
    `/sessions/${sessionId}`,
    payload,
    getSessionConfig(options)
  );
  return data;
};
