import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useTCOStore } from '@state/tcoStore';
import type { CalculationResponsePayload, SessionCreateResponsePayload, WizardData } from '@shared/types/tco.types';
import type { AxiosError } from 'axios';

vi.mock('@services/api', () => ({
  createSession: vi.fn(),
  updateSession: vi.fn(),
}));

const wizardData: WizardData = {
  currentVehicle: 'BEV001',
  comparisonVehicles: [],
  scenario: 'baseline',
  purchaseMethod: 'financed',
  dutyCycle: { urban: 60, regional: 25, longHaul: 15 },
  overrides: {},
  vehicleParamOverrides: {},
};

const sampleResult: CalculationResponsePayload = {
  vehicle_id: 'BEV001',
  scenario_name: 'baseline',
  total_cost: 1000,
  annual_cost: 100,
  cost_per_km: 1,
  breakdown: {
    npv_costs: {
      fuel_cost: 0,
      maintenance_cost: 0,
      battery_replacement_cost: 0,
      carbon_cost: 0,
      charging_labour_cost: 0,
      payload_penalty_cost: 0,
      payload_trip_multiplier_cost: 0,
      charging_dwell_opportunity_cost: 0,
      mr_downtime_opportunity_cost: 0,
      residual_value: 0,
    },
    nominal_costs: {
      insurance_cost: 0,
      registration_cost: 0,
      financing_cost: 0,
      depreciation: 0,
    },
    upfront_costs: {
      purchase_cost: 0,
      taxes_and_fees: 0,
    },
  },
};

const sampleResultUpdated: CalculationResponsePayload = {
  ...sampleResult,
  total_cost: 950,
  annual_cost: 95,
};

const wizardDataUpdated: WizardData = {
  ...wizardData,
  dutyCycle: { urban: 55, regional: 30, longHaul: 15 },
};

const makeSessionResponse = () => ({
  sessionId: 'session-123',
  status: 'completed' as const,
  wizardData,
  results: [sampleResult],
  updatedAt: new Date().toISOString(),
  lastCalculatedAt: new Date().toISOString(),
});

const makeAxiosStatusError = (status: number) =>
  ({
    isAxiosError: true,
    response: { status },
  }) as AxiosError;

describe('sessionLifecycle', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.resetAllMocks();
    useTCOStore.setState({ sessionId: undefined });
  });

  it('single-flights session creation and queues updates during create', async () => {
    const { createSession, updateSession } = await import('@services/api');
    let resolveCreate: (value: SessionCreateResponsePayload) => void;

    const createPromise = new Promise<SessionCreateResponsePayload>((resolve) => {
      resolveCreate = resolve;
    });

    const createSessionMock = vi.mocked(createSession);
    const updateSessionMock = vi.mocked(updateSession);

    createSessionMock.mockReturnValue(createPromise);
    updateSessionMock.mockResolvedValue(makeSessionResponse());

    const { persistSessionUpdate } = await import('@services/sessionLifecycle');

    const createOnly = persistSessionUpdate(
      { wizardData },
      { wizardData }
    );
    const queuedUpdate = persistSessionUpdate(
      { wizardData, results: [sampleResult] },
      { wizardData, results: [sampleResult] }
    );

    expect(createSessionMock).toHaveBeenCalledTimes(1);

    resolveCreate!({
      sessionId: 'session-123',
      status: 'draft',
      wizardData,
      results: [],
      updatedAt: new Date().toISOString(),
      lastCalculatedAt: null,
    });

    await Promise.all([createOnly, queuedUpdate]);

    expect(updateSessionMock).toHaveBeenCalledTimes(1);
    expect(updateSessionMock).toHaveBeenCalledWith(
      'session-123',
      { wizardData, results: [sampleResult] }
    );
  });

  it('field-merges queued wizard and results updates during create', async () => {
    const { createSession, updateSession } = await import('@services/api');
    let resolveCreate: (value: SessionCreateResponsePayload) => void;

    const createPromise = new Promise<SessionCreateResponsePayload>((resolve) => {
      resolveCreate = resolve;
    });

    const createSessionMock = vi.mocked(createSession);
    const updateSessionMock = vi.mocked(updateSession);

    createSessionMock.mockReturnValue(createPromise);
    updateSessionMock.mockResolvedValue(makeSessionResponse());

    const { persistSessionUpdate } = await import('@services/sessionLifecycle');

    const createOnly = persistSessionUpdate({ wizardData }, { wizardData });
    const queuedResultsOnly = persistSessionUpdate({ results: [sampleResult] }, { wizardData });
    const queuedWizardOnly = persistSessionUpdate({ wizardData: wizardDataUpdated }, { wizardData });

    resolveCreate!({
      sessionId: 'session-123',
      status: 'draft',
      wizardData,
      results: [],
      updatedAt: new Date().toISOString(),
      lastCalculatedAt: null,
    });

    await Promise.all([createOnly, queuedResultsOnly, queuedWizardOnly]);

    expect(updateSessionMock).toHaveBeenCalledTimes(1);
    expect(updateSessionMock).toHaveBeenCalledWith(
      'session-123',
      { wizardData: wizardDataUpdated, results: [sampleResult] }
    );
  });

  it('applies last-write-wins for repeated queued field updates', async () => {
    const { createSession, updateSession } = await import('@services/api');
    let resolveCreate: (value: SessionCreateResponsePayload) => void;

    const createPromise = new Promise<SessionCreateResponsePayload>((resolve) => {
      resolveCreate = resolve;
    });

    const createSessionMock = vi.mocked(createSession);
    const updateSessionMock = vi.mocked(updateSession);

    createSessionMock.mockReturnValue(createPromise);
    updateSessionMock.mockResolvedValue(makeSessionResponse());

    const { persistSessionUpdate } = await import('@services/sessionLifecycle');

    const createOnly = persistSessionUpdate({ wizardData }, { wizardData });
    const queuedResultsOld = persistSessionUpdate({ results: [sampleResult] }, { wizardData });
    const queuedResultsNew = persistSessionUpdate({ results: [sampleResultUpdated] }, { wizardData });

    resolveCreate!({
      sessionId: 'session-123',
      status: 'draft',
      wizardData,
      results: [],
      updatedAt: new Date().toISOString(),
      lastCalculatedAt: null,
    });

    await Promise.all([createOnly, queuedResultsOld, queuedResultsNew]);

    expect(updateSessionMock).toHaveBeenCalledTimes(1);
    expect(updateSessionMock).toHaveBeenCalledWith(
      'session-123',
      { results: [sampleResultUpdated] }
    );
  });

  it('retries transient session update failures', async () => {
    const { updateSession } = await import('@services/api');
    const { useTCOStore: lifecycleStore } = await import('@state/tcoStore');
    const updateSessionMock = vi.mocked(updateSession);
    const transientError = makeAxiosStatusError(503);

    lifecycleStore.setState({ sessionId: 'session-123' });
    updateSessionMock
      .mockRejectedValueOnce(transientError)
      .mockResolvedValueOnce(makeSessionResponse());

    const { persistSessionUpdate } = await import('@services/sessionLifecycle');

    await persistSessionUpdate({ wizardData }, { wizardData });

    expect(updateSessionMock).toHaveBeenCalledTimes(2);
  });

  it('does not retry non-transient session update failures', async () => {
    const { updateSession } = await import('@services/api');
    const { useTCOStore: lifecycleStore } = await import('@state/tcoStore');
    const updateSessionMock = vi.mocked(updateSession);
    const validationError = makeAxiosStatusError(400);

    lifecycleStore.setState({ sessionId: 'session-123' });
    updateSessionMock.mockRejectedValue(validationError);

    const { persistSessionUpdate } = await import('@services/sessionLifecycle');

    await expect(
      persistSessionUpdate({ wizardData }, { wizardData })
    ).rejects.toBe(validationError);
    expect(updateSessionMock).toHaveBeenCalledTimes(1);
  });
});
