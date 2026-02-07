type TelemetryLevel = 'warning' | 'error';

type TelemetryContext = Record<string, unknown>;

interface ReportClientErrorInput {
  source: string;
  error: unknown;
  context?: TelemetryContext;
  level?: TelemetryLevel;
}

interface ClientTelemetryEvent {
  level: TelemetryLevel;
  source: string;
  message: string;
  errorName: string;
  stack?: string;
  context?: TelemetryContext;
  timestamp: string;
  pathname: string;
  userAgent?: string;
}

const MAX_CONTEXT_DEPTH = 4;
const MAX_CONTEXT_KEYS = 20;
const MAX_STRING_LENGTH = 240;
const MAX_STACK_LENGTH = 1500;
const REDACTED = '[REDACTED]';
const TRUNCATED = '[TRUNCATED]';

const SENSITIVE_KEY_PATTERN =
  /pass(word)?|secret|token|authorization|cookie|session|api[_-]?key|credential/i;

const truncateString = (value: string, maxLength = MAX_STRING_LENGTH): string => {
  if (value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, maxLength)}...${TRUNCATED}`;
};

export const sanitizeTelemetryValue = (value: unknown, depth = 0): unknown => {
  if (value == null || typeof value === 'number' || typeof value === 'boolean') {
    return value;
  }

  if (typeof value === 'string') {
    return truncateString(value);
  }

  if (depth >= MAX_CONTEXT_DEPTH) {
    return TRUNCATED;
  }

  if (Array.isArray(value)) {
    return value.slice(0, MAX_CONTEXT_KEYS).map((item) => sanitizeTelemetryValue(item, depth + 1));
  }

  if (typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>).slice(0, MAX_CONTEXT_KEYS);
    return Object.fromEntries(
      entries.map(([key, currentValue]) => {
        if (SENSITIVE_KEY_PATTERN.test(key)) {
          return [key, REDACTED];
        }
        return [key, sanitizeTelemetryValue(currentValue, depth + 1)];
      })
    );
  }

  return String(value);
};

const normalizeError = (
  error: unknown
): Pick<ClientTelemetryEvent, 'message' | 'errorName' | 'stack'> => {
  if (error instanceof Error) {
    return {
      message: truncateString(error.message || 'Unknown error'),
      errorName: error.name || 'Error',
      stack: error.stack ? truncateString(error.stack, MAX_STACK_LENGTH) : undefined,
    };
  }

  return {
    message: truncateString(typeof error === 'string' ? error : 'Unknown error'),
    errorName: 'UnknownError',
    stack: undefined,
  };
};

const telemetryEndpoint = (): string | null => {
  const enabled = import.meta.env.VITE_CLIENT_TELEMETRY_ENABLED === 'true';
  const url = import.meta.env.VITE_CLIENT_TELEMETRY_URL?.trim();
  if (!enabled || !url) {
    return null;
  }
  return url;
};

const postTelemetryEvent = (url: string, event: ClientTelemetryEvent): void => {
  const body = JSON.stringify(event);

  if (typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
    const accepted = navigator.sendBeacon(url, new Blob([body], { type: 'application/json' }));
    if (accepted) {
      return;
    }
  }

  if (typeof fetch !== 'function') {
    return;
  }

  void fetch(url, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
    },
    body,
    keepalive: true,
    credentials: 'omit',
    mode: 'cors',
  }).catch(() => undefined);
};

export const reportClientError = ({
  source,
  error,
  context,
  level = 'error',
}: ReportClientErrorInput): void => {
  const normalizedError = normalizeError(error);
  const sanitizedContext = context ? (sanitizeTelemetryValue(context) as TelemetryContext) : undefined;

  if (level === 'error') {
    console.error(`[${source}] ${normalizedError.message}`, error);
  } else {
    console.warn(`[${source}] ${normalizedError.message}`, error);
  }

  const endpoint = telemetryEndpoint();
  if (!endpoint) {
    return;
  }

  const event: ClientTelemetryEvent = {
    level,
    source,
    message: normalizedError.message,
    errorName: normalizedError.errorName,
    stack: normalizedError.stack,
    context: sanitizedContext,
    timestamp: new Date().toISOString(),
    pathname: typeof window !== 'undefined' ? window.location.pathname : '',
    userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
  };

  postTelemetryEvent(endpoint, event);
};
