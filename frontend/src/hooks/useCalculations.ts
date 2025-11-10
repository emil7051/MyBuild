import { useMutation } from '@tanstack/react-query';
import { useCallback } from 'react';
import { calculateComparison, calculateTco } from '@shared/calculator';
import type {
  CalculationRequestPayload,
  CalculationResponsePayload,
  ComparisonRequestPayload,
} from '@shared/types/tco.types';
import { runCalculation, runComparison, createSession, updateSession } from '@services/api';
import { useTCOStore } from '@state/tcoStore';
import { buildSessionPayload } from '@utils/payload';

export const useCalculationRunner = () => {
  const setResults = useTCOStore((state) => state.setResults);
  const setIsCalculating = useTCOStore((state) => state.setIsCalculating);
  const wizardData = useTCOStore((state) => state.wizardData);
  const sessionId = useTCOStore((state) => state.sessionId);
  const setSessionId = useTCOStore((state) => state.setSessionId);

  const persistSession = useCallback(
    async (data: CalculationResponsePayload[]) => {
      if (!wizardData.currentVehicle || !data.length) {
        return;
      }
      const payload = buildSessionPayload(wizardData, data);
      try {
        const response = sessionId
          ? await updateSession(sessionId, payload)
          : await createSession(payload);
        setSessionId(response.sessionId);
      } catch (error) {
        console.warn('Failed to persist session', error);
      }
    },
    [sessionId, setSessionId, wizardData]
  );

  const comparisonMutation = useMutation({
    mutationFn: async (payload: ComparisonRequestPayload) => {
      try {
        return calculateComparison(payload);
      } catch (error) {
        console.warn('Local comparison failed — falling back to API.', error);
        return runComparison(payload);
      }
    },
    onMutate: () => setIsCalculating(true),
    onSuccess: (data) => {
      setResults(data);
      void persistSession(data);
    },
    onSettled: () => setIsCalculating(false),
  });

  const singleMutation = useMutation({
    mutationFn: async (payload: CalculationRequestPayload) => {
      try {
        return calculateTco(payload);
      } catch (error) {
        console.warn('Local calculation failed — falling back to API.', error);
        return runCalculation(payload);
      }
    },
    onMutate: () => setIsCalculating(true),
    onSuccess: (data) => {
      setResults([data]);
      void persistSession([data]);
    },
    onSettled: () => setIsCalculating(false),
  });

  return {
    runComparison: comparisonMutation.mutateAsync,
    runSingle: singleMutation.mutateAsync,
    comparisonStatus: comparisonMutation.status,
    singleStatus: singleMutation.status,
  };
};
