import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { useTCOStore } from '@state/tcoStore';
import { persistSessionUpdate } from '@services/sessionLifecycle';
import { sanitizeWizardData } from '@utils/payload';

export const useWizardAutosave = () => {
  const wizardData = useTCOStore((state) => state.wizardData);
  const sessionId = useTCOStore((state) => state.sessionId);
  const hasHydrated = useTCOStore((state) => state._hasHydrated);
  const lastSnapshot = useRef<string>('');
  const abortControllerRef = useRef<AbortController | null>(null);
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

    // If no sessionId exists, create a new session immediately
    if (!sessionId) {
      if (!wizardData.currentVehicle) {
        return;
      }

      setSaveStatus('saving');
      persistSessionUpdate({ wizardData: payload }, { wizardData: payload })
        .then(() => {
          lastSnapshot.current = serialized;
          setSaveStatus('idle');
        })
        .catch((error) => {
          console.warn('Failed to create session for autosave', error);
          setSaveStatus('error');
          toast.error('Not saved. Session creation failed.', {
            id: 'session-create-error',
            duration: 5000,
          });
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

      persistSessionUpdate({ wizardData: payload }, { wizardData: payload }, { signal })
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
  }, [hasHydrated, sessionId, wizardData]);

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
