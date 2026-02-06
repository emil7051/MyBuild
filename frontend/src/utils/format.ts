const BASE_CURRENCY_OPTIONS: Intl.NumberFormatOptions = {
  style: 'currency',
  currency: 'AUD',
  maximumFractionDigits: 0,
};

const LOCALE = 'en-AU';
const formatterCache = new Map<string, Intl.NumberFormat>();

const getFormatterCacheKey = (options: Intl.NumberFormatOptions): string => {
  const normalizedOptions = Object.entries(options)
    .filter(([, value]) => value !== undefined)
    .sort(([left], [right]) => left.localeCompare(right));
  return JSON.stringify(normalizedOptions);
};

const getFormatter = (options: Intl.NumberFormatOptions): Intl.NumberFormat => {
  const key = getFormatterCacheKey(options);
  const cached = formatterCache.get(key);
  if (cached) {
    return cached;
  }

  const formatter = new Intl.NumberFormat(LOCALE, options);
  formatterCache.set(key, formatter);
  return formatter;
};

export const formatCurrency = (
  value: number,
  options?: Intl.NumberFormatOptions
): string => {
  const resolvedOptions = {
    ...BASE_CURRENCY_OPTIONS,
    ...options,
  };

  return getFormatter(resolvedOptions).format(value);
};

export const formatCurrencyCompact = (value: number): string => {
  return getFormatter({
    style: 'currency',
    currency: 'AUD',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
};

export const formatPerKilometre = (value: number): string => {
  return `${formatCurrency(value, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} / km`;
};
