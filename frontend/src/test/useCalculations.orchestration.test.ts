import React, { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createRoot, type Root } from 'react-dom/client';
import { act } from 'react';
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  resetCalculationRunnerStateForTests,
  useCalculationRunner,
} from '@hooks/useCalculations';
import { useTCOStore } from '@state/tcoStore';
import { calculateComparison } from '@shared/calculator';
import { persistSessionUpdate } from '@services/sessionLifecycle';
import type {
  CalculationResponsePayload,
  ComparisonRequestPayload,
} from '@shared/types/tco.types';

vi.mock('@shared/calculator', () => ({
  calculateComparison: vi.fn(),
}));

vi.mock('@services/sessionLifecycle', () => ({
  persistSessionUpdate: vi.fn(),
}));

vi.mock('react-hot-toast', () => ({
  default: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

type RunnerHandle = ReturnType<typeof useCalculationRunner>;
const globalReactAct = globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean };
const previousActEnvironment = globalReactAct.IS_REACT_ACT_ENVIRONMENT;

interface Deferred<T> {
  promise: Promise<T>;
  resolve: (value: T | PromiseLike<T>) => void;
  reject: (reason?: unknown) => void;
}

const createDeferred = <T,>(): Deferred<T> => {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;

  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });

  return { promise, resolve, reject };
};

const createComparisonPayload = (): ComparisonRequestPayload => ({
  vehicle_ids: ['DSL001', 'BEV001'],
  scenario_name: 'baseline',
  purchase_method: 'financed',
  duty_cycle: {
    urban: 60,
    regional: 25,
    longHaul: 15,
  },
});

const createAlternateComparisonPayload = (): ComparisonRequestPayload => ({
  vehicle_ids: ['DSL001', 'BEV002'],
  scenario_name: 'baseline',
  purchase_method: 'financed',
  duty_cycle: {
    urban: 55,
    regional: 30,
    longHaul: 15,
  },
});

const createResult = (vehicleId: string): CalculationResponsePayload => ({
  vehicle_id: vehicleId,
  scenario_name: 'baseline',
  total_cost: 100000,
  annual_cost: 10000,
  cost_per_km: 1,
  breakdown: {} as CalculationResponsePayload['breakdown'],
});

const resetStoreState = (): void => {
  useTCOStore.setState({
    stepIndex: 0,
    wizardData: {
      currentVehicle: undefined,
      comparisonVehicles: [],
      scenario: 'baseline',
      purchaseMethod: 'financed',
      dutyCycle: {
        urban: 60,
        regional: 25,
        longHaul: 15,
      },
      overrides: {},
      vehicleParamOverrides: {},
    },
    results: [],
    isCalculating: false,
    calculationInFlightCount: 0,
    sessionId: undefined,
    latestRequestId: 0,
  });
};

const RunnerProbe = ({ onReady }: { onReady: (runner: RunnerHandle) => void }) => {
  const runner = useCalculationRunner();

  useEffect(() => {
    onReady(runner);
  }, [onReady, runner]);

  return null;
};

const mountRunnerProbes = async (count: number): Promise<{
  runners: RunnerHandle[];
  cleanup: () => Promise<void>;
}> => {
  const container = document.createElement('div');
  document.body.appendChild(container);

  const root: Root = createRoot(container);
  const queryClient = new QueryClient({
    defaultOptions: {
      mutations: {
        retry: false,
      },
    },
  });

  const runners: Array<RunnerHandle | null> = Array.from({ length: count }, () => null);

  await act(async () => {
    root.render(
      React.createElement(
        QueryClientProvider,
        { client: queryClient },
        React.createElement(
          React.Fragment,
          null,
          ...Array.from({ length: count }, (_, index) =>
            React.createElement(RunnerProbe, {
              key: index,
              onReady: (runner) => {
                runners[index] = runner;
              },
            })
          )
        )
      )
    );
  });

  if (runners.some((runner) => runner === null)) {
    throw new Error('Failed to initialize calculation runner probes.');
  }

  return {
    runners: runners as RunnerHandle[],
    cleanup: async () => {
      await act(async () => {
        root.unmount();
      });
      queryClient.clear();
      container.remove();
    },
  };
};

describe('useCalculationRunner orchestration', () => {
  beforeAll(() => {
    globalReactAct.IS_REACT_ACT_ENVIRONMENT = true;
  });

  afterAll(() => {
    globalReactAct.IS_REACT_ACT_ENVIRONMENT = previousActEnvironment;
  });

  beforeEach(() => {
    vi.mocked(calculateComparison).mockReset();
    vi.mocked(persistSessionUpdate).mockReset();

    resetCalculationRunnerStateForTests();
    resetStoreState();
  });

  it('deduplicates identical comparison requests across separate hook instances', async () => {
    const deferredComparison = createDeferred<CalculationResponsePayload[]>();
    vi.mocked(calculateComparison).mockImplementation(
      () => deferredComparison.promise as unknown as CalculationResponsePayload[]
    );

    const mounted = await mountRunnerProbes(2);

    try {
      const [runnerA, runnerB] = mounted.runners;
      const payload = createComparisonPayload();

      let firstRunPromise!: Promise<unknown>;
      let secondRunPromise!: Promise<unknown>;

      await act(async () => {
        firstRunPromise = runnerA.runComparison(payload);
        secondRunPromise = runnerB.runComparison(payload);
        await Promise.resolve();
      });

      expect(calculateComparison).toHaveBeenCalledTimes(1);
      expect(useTCOStore.getState().isCalculating).toBe(true);
      expect(useTCOStore.getState().calculationInFlightCount).toBe(1);

      await act(async () => {
        deferredComparison.resolve([createResult('DSL001'), createResult('BEV001')]);
        await firstRunPromise;
        await secondRunPromise;
      });

      expect(useTCOStore.getState().isCalculating).toBe(false);
      expect(useTCOStore.getState().calculationInFlightCount).toBe(0);
    } finally {
      await mounted.cleanup();
    }
  });

  it('keeps loading active until overlapping comparison calculations settle', async () => {
    const deferredComparisonA = createDeferred<CalculationResponsePayload[]>();
    const deferredComparisonB = createDeferred<CalculationResponsePayload[]>();

    vi.mocked(calculateComparison)
      .mockImplementationOnce(
        () => deferredComparisonA.promise as unknown as CalculationResponsePayload[]
      )
      .mockImplementationOnce(
        () => deferredComparisonB.promise as unknown as CalculationResponsePayload[]
      );

    const mounted = await mountRunnerProbes(2);

    try {
      const [runnerA, runnerB] = mounted.runners;

      let firstComparisonPromise!: Promise<unknown>;
      let secondComparisonPromise!: Promise<unknown>;

      await act(async () => {
        firstComparisonPromise = runnerA.runComparison(createComparisonPayload());
        secondComparisonPromise = runnerB.runComparison(createAlternateComparisonPayload());
        await Promise.resolve();
      });

      expect(calculateComparison).toHaveBeenCalledTimes(2);
      expect(useTCOStore.getState().isCalculating).toBe(true);
      expect(useTCOStore.getState().calculationInFlightCount).toBe(2);

      await act(async () => {
        deferredComparisonA.resolve([createResult('DSL001'), createResult('BEV001')]);
        await firstComparisonPromise;
      });

      expect(useTCOStore.getState().isCalculating).toBe(true);
      expect(useTCOStore.getState().calculationInFlightCount).toBe(1);

      await act(async () => {
        deferredComparisonB.resolve([createResult('DSL001'), createResult('BEV002')]);
        await secondComparisonPromise;
      });

      expect(useTCOStore.getState().isCalculating).toBe(false);
      expect(useTCOStore.getState().calculationInFlightCount).toBe(0);
    } finally {
      await mounted.cleanup();
    }
  });
});
