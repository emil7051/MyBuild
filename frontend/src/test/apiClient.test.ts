import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { SessionResponsePayload, WizardData } from '@shared/types/tco.types';

const axiosMocks = vi.hoisted(() => {
  const get = vi.fn();
  const post = vi.fn();
  const put = vi.fn();
  const create = vi.fn(() => ({ get, post, put }));
  return { get, post, put, create };
});

vi.mock('axios', () => ({
  default: {
    create: axiosMocks.create,
  },
}));

const wizardData: WizardData = {
  currentVehicle: 'BEV001',
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
};

const makeSessionResponse = (): SessionResponsePayload => ({
  sessionId: 'session-123',
  status: 'draft',
  wizardData,
  results: [],
  updatedAt: '2026-02-07T00:00:00.000Z',
  lastCalculatedAt: null,
});

describe('api.getSession', () => {
  beforeEach(() => {
    vi.resetModules();
    axiosMocks.get.mockReset();
    axiosMocks.post.mockReset();
    axiosMocks.put.mockReset();
    axiosMocks.create.mockClear();
  });

  it('returns the backend session payload', async () => {
    const expected = makeSessionResponse();
    axiosMocks.get.mockResolvedValue({ data: expected });

    const { getSession } = await import('@services/api');
    const response = await getSession(expected.sessionId);

    expect(axiosMocks.get).toHaveBeenCalledTimes(1);
    expect(axiosMocks.get).toHaveBeenCalledWith(`/sessions/${expected.sessionId}`, {});
    expect(response).toEqual(expected);
  });
});
