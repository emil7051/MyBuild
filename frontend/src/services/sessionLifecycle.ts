import axios from 'axios';
import { createSession, updateSession } from '@services/api';
import { reportClientError } from '@services/clientTelemetry';
import { useTCOStore } from '@state/tcoStore';
import type {
  SessionCreatePayload,
  SessionCreateResponsePayload,
  SessionUpdatePayload,
} from '@shared/types/tco.types';

type PendingUpdate = {
  payload: SessionUpdatePayload;
  fieldTimestamps: Partial<Record<keyof SessionUpdatePayload, number>>;
};

let createInFlight: Promise<SessionCreateResponsePayload> | null = null;
let pendingUpdate: PendingUpdate | null = null;

const RETRYABLE_STATUS_CODES = new Set([408, 429, 500, 502, 503, 504]);
const MAX_RETRY_ATTEMPTS = 3;
const RETRY_DELAY_MS = 250;

// During initial session creation, queued updates are merged by top-level field
// so wizard-only and results updates cannot overwrite each other accidentally.
const PENDING_UPDATE_FIELDS: (keyof SessionUpdatePayload)[] = [
  'wizardData',
  'results',
  'operatorProfile',
  'feedback',
];

const isPlainObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const mergeFieldValue = (existingValue: unknown, incomingValue: unknown): unknown => {
  if (!isPlainObject(existingValue) || !isPlainObject(incomingValue)) {
    return incomingValue;
  }

  const merged: Record<string, unknown> = { ...existingValue };
  Object.entries(incomingValue).forEach(([key, value]) => {
    if (value === undefined) {
      return;
    }
    merged[key] = mergeFieldValue(merged[key], value);
  });

  return merged;
};

const sleep = (ms: number) => new Promise((resolve) => {
  setTimeout(resolve, ms);
});

const isTransientSessionError = (error: unknown): boolean => {
  if (axios.isCancel(error) || (error instanceof Error && error.name === 'CanceledError')) {
    return false;
  }

  if (!axios.isAxiosError(error)) {
    return true;
  }

  if (!error.response) {
    return true;
  }

  return RETRYABLE_STATUS_CODES.has(error.response.status);
};

const withTransientRetry = async <T>(operation: () => Promise<T>): Promise<T> => {
  let attempt = 1;

  while (attempt <= MAX_RETRY_ATTEMPTS) {
    try {
      return await operation();
    } catch (error) {
      if (!isTransientSessionError(error) || attempt === MAX_RETRY_ATTEMPTS) {
        throw error;
      }

      await sleep(RETRY_DELAY_MS * attempt);
      attempt += 1;
    }
  }

  throw new Error('Retry loop exited unexpectedly');
};

const enqueuePendingUpdate = (payload: SessionUpdatePayload) => {
  if (!pendingUpdate) {
    pendingUpdate = {
      payload: {},
      fieldTimestamps: {},
    };
  }

  const queued = pendingUpdate;
  if (!queued) {
    return;
  }
  const queuedPayload = queued.payload as Partial<Record<keyof SessionUpdatePayload, unknown>>;

  const timestamp = Date.now();

  PENDING_UPDATE_FIELDS.forEach((field) => {
    if (!Object.prototype.hasOwnProperty.call(payload, field)) {
      return;
    }

    if (timestamp < (queued.fieldTimestamps[field] ?? -Infinity)) {
      return;
    }

    const incomingValue = payload[field];

    if (incomingValue === undefined) {
      delete queuedPayload[field];
      queued.fieldTimestamps[field] = timestamp;
      return;
    }

    queuedPayload[field] = mergeFieldValue(
      queuedPayload[field],
      incomingValue
    );
    queued.fieldTimestamps[field] = timestamp;
  });
};

const flushPendingUpdates = async (
  sessionId: string
): Promise<void> => {
  const mergedPayload = pendingUpdate?.payload;
  pendingUpdate = null;

  const safeUpdate = async (payload: SessionUpdatePayload): Promise<void> => {
    try {
      await withTransientRetry(() => updateSession(sessionId, payload));
    } catch (error) {
      reportClientError({
        source: 'sessionLifecycle.flushPendingUpdates',
        error,
        level: 'warning',
        context: {
          sessionId,
        },
      });
      throw error;
    }
  };

  if (mergedPayload && Object.keys(mergedPayload).length > 0) {
    await safeUpdate(mergedPayload);
  }
};

export const persistSessionUpdate = async (
  updatePayload: SessionUpdatePayload,
  createPayload: SessionCreatePayload,
  options: { signal?: AbortSignal } = {}
) => {
  const { sessionId, setSessionId } = useTCOStore.getState();

  if (sessionId) {
    return withTransientRetry(() =>
      updateSession(sessionId, updatePayload, {
        signal: options.signal,
      })
    );
  }

  if (createInFlight) {
    enqueuePendingUpdate(updatePayload);
    return createInFlight;
  }

  createInFlight = withTransientRetry(() => createSession(createPayload))
    .then((response) => {
      setSessionId(response.sessionId);
      return response;
    })
    .then(async (response) => {
      await flushPendingUpdates(response.sessionId);
      return response;
    })
    .finally(() => {
      createInFlight = null;
    });

  return createInFlight;
};
