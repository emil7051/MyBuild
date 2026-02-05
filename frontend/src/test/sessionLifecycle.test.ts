import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useTCOStore } from '@state/tcoStore';
import type { CalculationResponsePayload, SessionCreateResponsePayload, WizardData } from '@shared/types/tco.types';

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
    purchase_cost: 0,
    fuel_cost: 0,
    maintenance_cost: 0,
    insurance_cost: 0,
    registration_cost: 0,
    battery_replacement_cost: 0,
    financing_cost: 0,
    carbon_cost: 0,
    charging_labour_cost: 0,
    payload_penalty_cost: 0,
    residual_value: 0,
    depreciation: 0,
    taxes_and_fees: 0,
  },
};

describe('sessionLifecycle', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    useTCOStore.setState({ sessionId: undefined, sessionSecret: undefined });
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
    updateSessionMock.mockResolvedValue({
      sessionId: 'session-123',
      status: 'completed',
      wizardData,
      results: [sampleResult],
      updatedAt: new Date().toISOString(),
      lastCalculatedAt: new Date().toISOString(),
    });

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
      sessionSecret: 'secret-abc',
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
      { wizardData, results: [sampleResult] },
      { sessionSecret: 'secret-abc' }
    );
  });
});
