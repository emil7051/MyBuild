import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { useTCOStore } from '@state/tcoStore';
import { createSession, updateSession } from '@services/api';
import type { WizardData } from '@shared/types/tco.types';
import { compactOverrides, compactVehicleParamOverrides } from '@utils/payload';

const sanitizeWizardData = (wizardData: WizardData): WizardData => {
  const overrides = compactOverrides(wizardData.overrides ?? {});
  const vehicleOverrides = compactVehicleParamOverrides(
    wizardData.vehicleParamOverrides ?? {}
  );

  return {
    ...wizardData,
    overrides: Object.keys(overrides).length ? overrides : undefined,
    vehicleParamOverrides: Object.keys(vehicleOverrides).length
      ? vehicleOverrides
      : undefined,
  };
};

export const useWizardAutosave = () => {
  const wizardData = useTCOStore((state) => state.wizardData);
  const sessionId = useTCOStore((state) => state.sessionId);
  const sessionSecret = useTCOStore((state) => state.sessionSecret);
  const setSessionId = useTCOStore((state) => state.setSessionId);
  const setSessionSecret = useTCOStore((state) => state.setSessionSecret);
  const hasHydrated = useTCOStore((state) => state._hasHydrated);
  const lastSnapshot = useRef<string>('');
  const abortControllerRef = useRef<AbortController | null>(null);
  const isCreatingSessionRef = useRef(false);
  const pendingAutosaveRef = useRef<WizardData | null>(null);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'error'>('idle');

  useEffect(() => {
    // Wait for store to hydrate before attempting any session operations
    // This prevents race conditions where we try to create a session
    // before the persisted sessionId is loaded from localStorage
    if (!hasHydrated) {
      return;
    }

    const payload = sanitizeWizardData(wizardData);
    const serialized = JSON.stringify(payload);
    if (serialized === lastSnapshot.current) {
      return;
    }

    // If no sessionId exists, queue the autosave data
    if (!sessionId) {
      // If we're already creating a session, queue this data
      if (isCreatingSessionRef.current) {
        pendingAutosaveRef.current = payload;
        return;
      }

      // Only create session if we have a vehicle selected
      if (!wizardData.currentVehicle) {
        return;
      }

      // Create a new session
      isCreatingSessionRef.current = true;
      setSaveStatus('saving');

      createSession({ wizardData: payload })
        .then((response) => {
          setSessionId(response.sessionId);
          setSessionSecret(response.sessionSecret);
          lastSnapshot.current = serialized;
          setSaveStatus('idle');

          // If there's pending data that changed while we were creating the session, send it
          if (pendingAutosaveRef.current) {
            const pendingData = pendingAutosaveRef.current;
            pendingAutosaveRef.current = null;
            const pendingSerialized = JSON.stringify(pendingData);
            if (pendingSerialized !== serialized) {
              updateSession(response.sessionId, { wizardData: pendingData }, {
                sessionSecret: response.sessionSecret,
              }).catch((error) => {
                console.warn('Pending autosave failed', error);
              });
              lastSnapshot.current = pendingSerialized;
            }
          }
        })
        .catch((error) => {
          console.warn('Failed to create session for autosave', error);
          setSaveStatus('error');
          toast.error('Not saved. Session creation failed.', {
            id: 'session-create-error',
            duration: 5000,
          });
        })
        .finally(() => {
          isCreatingSessionRef.current = false;
        });

      return;
    }

    const timer = setTimeout(() => {
      // Cancel any in-flight autosave request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create a new AbortController for this request
      abortControllerRef.current = new AbortController();
      const signal = abortControllerRef.current.signal;

      lastSnapshot.current = serialized;
      setSaveStatus('saving');

      updateSession(sessionId, { wizardData: payload }, { signal, sessionSecret })
        .then(() => {
          setSaveStatus('idle');
        })
        .catch((error) => {
          // Ignore aborted requests (they were cancelled intentionally)
          if (axios.isCancel(error) || error.name === 'CanceledError') {
            return;
          }
          console.warn('Autosave failed', error);
          setSaveStatus('error');
          toast.error('Auto-save failed. Your changes may not be saved.', {
            id: 'autosave-error',
            duration: 5000,
          });
          // Reset snapshot so it retries on next change
          lastSnapshot.current = '';
        });
    }, 800);

    return () => {
      clearTimeout(timer);
    };
  }, [hasHydrated, sessionId, sessionSecret, setSessionId, setSessionSecret, wizardData]);

  // Cleanup AbortController on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return { saveStatus };
};
