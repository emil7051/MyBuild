import axios from 'axios';
import type {
  SessionCreatePayload,
  SessionCreateResponsePayload,
  SessionResponsePayload,
  SessionUpdatePayload,
} from '@shared/types/tco.types';

const DEFAULT_API_BASE_URL = '/api/v1';
const LOCAL_API_HOSTS = new Set(['localhost', '127.0.0.1', '::1', '[::1]']);

export const resolveApiBaseUrl = (value: string | undefined): string => {
  const candidate = value?.trim();
  if (!candidate) {
    return DEFAULT_API_BASE_URL;
  }

  if (candidate.startsWith('/')) {
    return candidate;
  }

  let parsed: URL;
  try {
    parsed = new URL(candidate);
  } catch {
    throw new Error(
      'VITE_API_URL must be a relative API path or an absolute http(s) URL.'
    );
  }

  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    throw new Error('VITE_API_URL must use http or https.');
  }

  if (parsed.protocol === 'http:' && !LOCAL_API_HOSTS.has(parsed.hostname)) {
    throw new Error(
      'VITE_API_URL must use HTTPS unless pointing to localhost for development.'
    );
  }

  return candidate;
};

const api = axios.create({
  baseURL: resolveApiBaseUrl(import.meta.env.VITE_API_URL),
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

export const getSession = async (
  sessionId: string,
  options: SessionRequestOptions = {}
) => {
  const { data } = await api.get<SessionResponsePayload>(
    `/sessions/${sessionId}`,
    getSessionConfig(options)
  );
  return data;
};
