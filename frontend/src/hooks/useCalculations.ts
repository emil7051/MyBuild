import { useMutation } from '@tanstack/react-query';
import { useCallback } from 'react';
import toast from 'react-hot-toast';
import stableStringify from 'fast-json-stable-stringify';
import { calculateComparison } from '@shared/calculator';
import type {
  CalculationResponsePayload,
  ComparisonRequestPayload,
} from '@shared/types/tco.types';
import { reportClientError } from '@services/clientTelemetry';
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

const calculationRunnerState = {
  lastComparisonHash: null as string | null,
  inflightComparisonHashes: new Set<string>(),
};

export const resetCalculationRunnerStateForTests = (): void => {
  calculationRunnerState.lastComparisonHash = null;
  calculationRunnerState.inflightComparisonHashes.clear();
};

export const useCalculationRunner = () => {
  const setResults = useTCOStore((state) => state.setResults);
  const beginCalculation = useTCOStore((state) => state.beginCalculation);
  const finishCalculation = useTCOStore((state) => state.finishCalculation);
  const getNextRequestId = useTCOStore((state) => state.getNextRequestId);
  const wizardData = useTCOStore((state) => state.wizardData);

  const persistSession = useCallback(
    async (data: CalculationResponsePayload[]) => {
      if (!wizardData.currentVehicle || !data.length) {
        return;
      }

      const payload = buildSessionPayload(wizardData, data);
      try {
        await persistSessionUpdate(payload, payload);
      } catch (error) {
        reportClientError({
          source: 'useCalculationRunner.persistSession',
          error,
          level: 'warning',
          context: {
            resultsCount: data.length,
          },
        });
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
      beginCalculation();
    },
    onSuccess: ({ data, requestId, vehicleOrder }) => {
      setResults(data, requestId, vehicleOrder);
      void persistSession(data);
    },
    onError: (error) => {
      reportClientError({
        source: 'useCalculationRunner.runComparison',
        error,
        level: 'warning',
      });
      toast.error('Comparison failed. Please try again.', {
        id: 'comparison-error',
        duration: 5000,
      });
    },
    onSettled: () => {
      finishCalculation();
    },
  });

  return {
    runComparison: useCallback(
      async (payload: ComparisonRequestPayload) => {
        const hash = serializeForHash(payload);
        if (
          hash === calculationRunnerState.lastComparisonHash ||
          calculationRunnerState.inflightComparisonHashes.has(hash)
        ) {
          return;
        }
        calculationRunnerState.inflightComparisonHashes.add(hash);
        try {
          const result = await comparisonMutation.mutateAsync(payload);
          calculationRunnerState.lastComparisonHash = hash;
          return result;
        } finally {
          calculationRunnerState.inflightComparisonHashes.delete(hash);
        }
      },
      [comparisonMutation]
    ),
  };
};
