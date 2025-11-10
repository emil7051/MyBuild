const BASE_CURRENCY_OPTIONS: Intl.NumberFormatOptions = {
  style: 'currency',
  currency: 'AUD',
  maximumFractionDigits: 0,
};

export const formatCurrency = (
  value: number,
  options?: Intl.NumberFormatOptions
): string => {
  return new Intl.NumberFormat('en-AU', {
    ...BASE_CURRENCY_OPTIONS,
    ...options,
  }).format(value);
};

export const formatCurrencyCompact = (value: number): string => {
  return new Intl.NumberFormat('en-AU', {
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
