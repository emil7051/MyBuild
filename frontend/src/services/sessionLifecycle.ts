import axios from 'axios';
import { createSession, updateSession } from '@services/api';
import { useTCOStore } from '@state/tcoStore';
import type {
  SessionCreatePayload,
  SessionCreateResponsePayload,
  SessionUpdatePayload,
} from '@shared/types/tco.types';

type PendingUpdate = {
  payload: SessionUpdatePayload;
  timestamp: number;
  hasResults: boolean;
};

let createInFlight: Promise<SessionCreateResponsePayload> | null = null;
let pendingWizardUpdate: PendingUpdate | null = null;
let pendingResultsUpdate: PendingUpdate | null = null;

const RETRYABLE_STATUS_CODES = new Set([408, 429, 500, 502, 503, 504]);
const MAX_RETRY_ATTEMPTS = 3;
const RETRY_DELAY_MS = 250;

const hasResultsPayload = (payload: SessionUpdatePayload) =>
  Object.prototype.hasOwnProperty.call(payload, 'results');

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
  const pending = {
    payload,
    timestamp: Date.now(),
    hasResults: hasResultsPayload(payload),
  };

  if (pending.hasResults) {
    pendingResultsUpdate = pending;
  } else {
    pendingWizardUpdate = pending;
  }
};

const flushPendingUpdates = async (
  sessionId: string
): Promise<void> => {
  const resultsUpdate = pendingResultsUpdate;
  const wizardUpdate = pendingWizardUpdate;

  pendingResultsUpdate = null;
  pendingWizardUpdate = null;

  const safeUpdate = async (payload: SessionUpdatePayload): Promise<void> => {
    try {
      await withTransientRetry(() => updateSession(sessionId, payload));
    } catch (error) {
      console.warn('Failed to flush pending session update', error);
      throw error;
    }
  };

  if (resultsUpdate && wizardUpdate) {
    if (wizardUpdate.timestamp > resultsUpdate.timestamp) {
      await safeUpdate(resultsUpdate.payload);
      await safeUpdate(wizardUpdate.payload);
      return;
    }
    await safeUpdate(resultsUpdate.payload);
    return;
  }

  if (resultsUpdate) {
    await safeUpdate(resultsUpdate.payload);
    return;
  }

  if (wizardUpdate) {
    await safeUpdate(wizardUpdate.payload);
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
