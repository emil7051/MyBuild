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

const hasResultsPayload = (payload: SessionUpdatePayload) =>
  Object.prototype.hasOwnProperty.call(payload, 'results');

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
  sessionId: string,
  sessionSecret: string
): Promise<void> => {
  const resultsUpdate = pendingResultsUpdate;
  const wizardUpdate = pendingWizardUpdate;

  pendingResultsUpdate = null;
  pendingWizardUpdate = null;

  const safeUpdate = async (payload: SessionUpdatePayload) => {
    try {
      await updateSession(sessionId, payload, { sessionSecret });
    } catch (error) {
      console.warn('Failed to flush pending session update', error);
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
  const { sessionId, sessionSecret, setSessionId, setSessionSecret } =
    useTCOStore.getState();

  if (sessionId) {
    return updateSession(sessionId, updatePayload, {
      sessionSecret,
      signal: options.signal,
    });
  }

  if (createInFlight) {
    enqueuePendingUpdate(updatePayload);
    return createInFlight;
  }

  createInFlight = createSession(createPayload)
    .then((response) => {
      setSessionId(response.sessionId);
      setSessionSecret(response.sessionSecret);
      return response;
    })
    .then(async (response) => {
      await flushPendingUpdates(response.sessionId, response.sessionSecret);
      return response;
    })
    .finally(() => {
      createInFlight = null;
    });

  return createInFlight;
};
