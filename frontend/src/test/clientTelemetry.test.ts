import { afterEach, describe, expect, it, vi } from 'vitest';
import { reportClientError, sanitizeTelemetryValue } from '@services/clientTelemetry';

describe('clientTelemetry', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it('redacts sensitive fields from telemetry context', () => {
    const sanitized = sanitizeTelemetryValue({
      sessionToken: 'abc123',
      nested: {
        password: 'secret',
        safe: 'value',
      },
    });

    expect(sanitized).toEqual({
      sessionToken: '[REDACTED]',
      nested: {
        password: '[REDACTED]',
        safe: 'value',
      },
    });
  });

  it('does not emit network telemetry when disabled', () => {
    vi.stubEnv('VITE_CLIENT_TELEMETRY_ENABLED', 'false');
    vi.stubEnv('VITE_CLIENT_TELEMETRY_URL', 'https://example.test/telemetry');

    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined);

    reportClientError({
      source: 'clientTelemetry.test',
      error: new Error('warning path'),
      level: 'warning',
    });

    expect(fetchMock).not.toHaveBeenCalled();
    expect(warnSpy).toHaveBeenCalledTimes(1);
  });

  it('emits redacted telemetry payload when enabled', () => {
    vi.stubEnv('VITE_CLIENT_TELEMETRY_ENABLED', 'true');
    vi.stubEnv('VITE_CLIENT_TELEMETRY_URL', 'https://example.test/telemetry');

    Object.defineProperty(window.navigator, 'sendBeacon', {
      value: undefined,
      configurable: true,
    });

    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal('fetch', fetchMock);
    vi.spyOn(console, 'error').mockImplementation(() => undefined);

    reportClientError({
      source: 'clientTelemetry.test',
      error: new Error('boom'),
      context: {
        apiKey: 'token-123',
        nested: {
          cookie: 'session-cookie',
          safe: 'ok',
        },
      },
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);

    const [url, requestInit] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('https://example.test/telemetry');

    const body = JSON.parse(String(requestInit.body));
    expect(body.context.apiKey).toBe('[REDACTED]');
    expect(body.context.nested.cookie).toBe('[REDACTED]');
    expect(body.context.nested.safe).toBe('ok');
    expect(body.source).toBe('clientTelemetry.test');
  });
});
