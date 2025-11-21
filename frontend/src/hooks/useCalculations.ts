import { useMutation } from '@tanstack/react-query';
import { useCallback } from 'react';
import { calculateComparison, calculateTco } from '@shared/calculator';
import type {
  CalculationRequestPayload,
  CalculationResponsePayload,
  ComparisonRequestPayload,
} from '@shared/types/tco.types';
import {
  createSession,
  updateSession,
} from '@services/api';
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
      return calculateComparison(payload);
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
      return calculateTco(payload);
    },
    onMutate: () => setIsCalculating(true),
    onSuccess: (data) => {
      setResults([data]);
      void persistSession([data]);
    },
    onSettled: () => setIsCalculating(false),
  });

  const runPreviewComparison = useCallback(
    async (payload: ComparisonRequestPayload) => {
      if (!payload.vehicle_ids.length) {
        return;
      }
      setIsCalculating(true);
      try {
        const data = calculateComparison(payload);
        setResults(data);
      } catch (error) {
        console.warn('Preview comparison failed', error);
      } finally {
        setIsCalculating(false);
      }
    },
    [setIsCalculating, setResults]
  );

  return {
    runComparison: comparisonMutation.mutateAsync,
    runPreviewComparison,
    runSingle: singleMutation.mutateAsync,
    comparisonStatus: comparisonMutation.status,
    singleStatus: singleMutation.status,
  };
};
