import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
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

  afterEach(() => {
    vi.unstubAllEnvs();
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

  it('uses localhost HTTP API URLs in development', async () => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000/api/v1');

    await import('@services/api');

    expect(axiosMocks.create).toHaveBeenCalledTimes(1);
    expect(axiosMocks.create).toHaveBeenCalledWith(
      expect.objectContaining({
        baseURL: 'http://localhost:8000/api/v1',
        withCredentials: true,
      })
    );
  });

  it('rejects insecure non-localhost HTTP API URLs', async () => {
    vi.stubEnv('VITE_API_URL', 'http://example.com/api/v1');

    await expect(import('@services/api')).rejects.toThrow(
      'VITE_API_URL must use HTTPS unless pointing to localhost for development.'
    );
  });
});
