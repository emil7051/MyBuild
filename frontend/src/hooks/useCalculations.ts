import { useMutation } from '@tanstack/react-query';
import { useCallback, useRef } from 'react';
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

  // Mutex refs to prevent duplicate session creation race condition
  const isCreatingSession = useRef(false);
  const pendingSessionId = useRef<string | null>(null);

  const persistSession = useCallback(
    async (data: CalculationResponsePayload[]) => {
      if (!wizardData.currentVehicle || !data.length) {
        return;
      }

      // If we're already creating a session, skip this call
      if (isCreatingSession.current) {
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
