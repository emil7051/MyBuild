import { useMutation } from '@tanstack/react-query';
import { useCallback, useRef } from 'react';
import { calculateComparison, calculateTco } from '@shared/calculator';
import type {
  CalculationRequestPayload,
  CalculationResponsePayload,
  ComparisonRequestPayload,
} from '@shared/types/tco.types';
import { createSession, updateSession } from '@services/api';
import { useTCOStore } from '@state/tcoStore';
import { buildSessionPayload } from '@utils/payload';

const stableStringify = (value: unknown): string => {
  if (value === undefined || value === null) {
    return 'null';
  }
  if (Array.isArray(value)) {
    return `[${value.map(stableStringify).join(',')}]`;
  }
  if (typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>).sort(([a], [b]) =>
      a.localeCompare(b)
    );
    return `{${entries
      .map(([key, val]) => `${JSON.stringify(key)}:${stableStringify(val)}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
};

export const useCalculationRunner = () => {
  const setResults = useTCOStore((state) => state.setResults);
  const setIsCalculating = useTCOStore((state) => state.setIsCalculating);
  const getNextRequestId = useTCOStore((state) => state.getNextRequestId);
  const wizardData = useTCOStore((state) => state.wizardData);
  const sessionId = useTCOStore((state) => state.sessionId);
  const setSessionId = useTCOStore((state) => state.setSessionId);

  // Mutex refs to prevent duplicate session creation race condition
  const isCreatingSession = useRef(false);
  const pendingSessionId = useRef<string | null>(null);
  // Ref to store pending payload while session is being created
  const pendingPayload = useRef<CalculationResponsePayload[] | null>(null);
  const lastComparisonHash = useRef<string | null>(null);
  const inflightComparisonHash = useRef<string | null>(null);
  const lastSingleHash = useRef<string | null>(null);
  const inflightSingleHash = useRef<string | null>(null);

  const persistSession = useCallback(
    async (data: CalculationResponsePayload[]) => {
      if (!wizardData.currentVehicle || !data.length) {
        return;
      }

      // If we're already creating a session, queue this payload to send after create completes
      if (isCreatingSession.current) {
        pendingPayload.current = data;
        return;
      }

      const payload = buildSessionPayload(wizardData, data);
      const currentSessionId = sessionId || pendingSessionId.current;

      try {
        if (currentSessionId) {
          await updateSession(currentSessionId, payload);
        } else {
          isCreatingSession.current = true;
          const response = await createSession(payload);
          pendingSessionId.current = response.sessionId;
          setSessionId(response.sessionId);

          // After session creation completes, check if we have a pending payload to send
          if (pendingPayload.current) {
            const queuedData = pendingPayload.current;
            pendingPayload.current = null;
            const queuedPayload = buildSessionPayload(wizardData, queuedData);
            await updateSession(response.sessionId, queuedPayload);
          }
        }
      } catch (error) {
        console.warn('Failed to persist session', error);
      } finally {
        isCreatingSession.current = false;
      }
    },
    [sessionId, setSessionId, wizardData]
  );

  const comparisonMutation = useMutation({
    mutationFn: async (payload: ComparisonRequestPayload) => {
      // Capture request context before starting calculation
      const requestId = getNextRequestId();
      const vehicleOrder = payload.vehicle_ids;
      const data = await calculateComparison(payload);
      return { data, requestId, vehicleOrder };
    },
    onMutate: () => {
      setIsCalculating(true);
    },
    onSuccess: ({ data, requestId, vehicleOrder }) => {
      setResults(data, requestId, vehicleOrder);
      void persistSession(data);
    },
    onSettled: () => {
      setIsCalculating(false);
    },
  });

  const singleMutation = useMutation({
    mutationFn: async (payload: CalculationRequestPayload) => {
      // Capture request context before starting calculation
      const requestId = getNextRequestId();
      const vehicleOrder = [payload.vehicle_id];
      const data = await calculateTco(payload);
      return { data, requestId, vehicleOrder };
    },
    onMutate: () => setIsCalculating(true),
    onSuccess: ({ data, requestId, vehicleOrder }) => {
      setResults([data], requestId, vehicleOrder);
      void persistSession([data]);
    },
    onSettled: () => setIsCalculating(false),
  });

  return {
    runComparison: useCallback(
      async (payload: ComparisonRequestPayload) => {
        const hash = stableStringify(payload);
        if (hash === lastComparisonHash.current || hash === inflightComparisonHash.current) {
          return;
        }
        inflightComparisonHash.current = hash;
        try {
          const result = await comparisonMutation.mutateAsync(payload);
          lastComparisonHash.current = hash;
          return result;
        } finally {
          if (inflightComparisonHash.current === hash) {
            inflightComparisonHash.current = null;
          }
        }
      },
      [comparisonMutation]
    ),
    runSingle: useCallback(
      async (payload: CalculationRequestPayload) => {
        const hash = stableStringify(payload);
        if (hash === lastSingleHash.current || hash === inflightSingleHash.current) {
          return;
        }
        inflightSingleHash.current = hash;
        try {
          const result = await singleMutation.mutateAsync(payload);
          lastSingleHash.current = hash;
          return result;
        } finally {
          if (inflightSingleHash.current === hash) {
            inflightSingleHash.current = null;
          }
        }
      },
      [singleMutation]
    ),
    comparisonStatus: comparisonMutation.status,
    singleStatus: singleMutation.status,
  };
};
