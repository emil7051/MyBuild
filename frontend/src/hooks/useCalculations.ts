import { useMutation } from '@tanstack/react-query';
import { useCallback, useRef } from 'react';
import toast from 'react-hot-toast';
import stableStringify from 'fast-json-stable-stringify';
import { calculateComparison, calculateTco } from '@shared/calculator';
import type {
  CalculationRequestPayload,
  CalculationResponsePayload,
  ComparisonRequestPayload,
} from '@shared/types/tco.types';
import { persistSessionUpdate } from '@services/sessionLifecycle';
import { useTCOStore } from '@state/tcoStore';
import { buildSessionPayload } from '@utils/payload';

const UNDEFINED_SENTINEL = '__undefined__';

const normalizeForStableHash = (value: unknown): unknown => {
  if (value === undefined) {
    return UNDEFINED_SENTINEL;
  }

  if (value === null || typeof value !== 'object') {
    return value;
  }

  if (Array.isArray(value)) {
    return value.map((item) => normalizeForStableHash(item));
  }

  return Object.fromEntries(
    Object.entries(value as Record<string, unknown>).map(([key, currentValue]) => [
      key,
      normalizeForStableHash(currentValue),
    ])
  );
};

const serializeForHash = (value: unknown): string =>
  stableStringify(normalizeForStableHash(value));

export const useCalculationRunner = () => {
  const setResults = useTCOStore((state) => state.setResults);
  const setIsCalculating = useTCOStore((state) => state.setIsCalculating);
  const getNextRequestId = useTCOStore((state) => state.getNextRequestId);
  const wizardData = useTCOStore((state) => state.wizardData);
  const lastComparisonHash = useRef<string | null>(null);
  const inflightComparisonHash = useRef<string | null>(null);
  const lastSingleHash = useRef<string | null>(null);
  const inflightSingleHash = useRef<string | null>(null);

  const persistSession = useCallback(
    async (data: CalculationResponsePayload[]) => {
      if (!wizardData.currentVehicle || !data.length) {
        return;
      }

      const payload = buildSessionPayload(wizardData, data);
      try {
        await persistSessionUpdate(payload, payload);
      } catch (error) {
        console.warn('Failed to persist session', error);
        toast.error('Results calculated, but saving failed. We will retry automatically.', {
          id: 'persist-session-error',
          duration: 5000,
        });
      }
    },
    [wizardData]
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
    onError: (error) => {
      console.warn('Comparison calculation failed', error);
      toast.error('Comparison failed. Please try again.', {
        id: 'comparison-error',
        duration: 5000,
      });
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
    onError: (error) => {
      console.warn('Single-vehicle calculation failed', error);
      toast.error('Calculation failed. Please try again.', {
        id: 'single-calculation-error',
        duration: 5000,
      });
    },
    onSettled: () => setIsCalculating(false),
  });

  return {
    runComparison: useCallback(
      async (payload: ComparisonRequestPayload) => {
        const hash = serializeForHash(payload);
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
        const hash = serializeForHash(payload);
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
