import type { InputHTMLAttributes } from 'react';
import clsx from 'clsx';

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  error?: string;
}

const Field = ({ label, hint, error, className, ...props }: FieldProps) => (
  <label className="flex flex-col gap-1 text-sm text-slate-700">
    <span className="font-medium text-slate-900">{label}</span>
    <input
      className={clsx(
        'rounded-lg border bg-white px-3 py-2 text-base text-slate-900 shadow-sm focus:outline-none focus:ring-2',
        error
          ? 'border-rose-400 focus:border-rose-400 focus:ring-rose-100'
          : 'border-slate-200 focus:border-brand-400 focus:ring-brand-100',
        className
      )}
      aria-invalid={Boolean(error)}
      {...props}
    />
    {error ? (
      <span className="text-xs text-rose-600">{error}</span>
    ) : (
      hint && <span className="text-xs text-slate-500">{hint}</span>
    )}
  </label>
);

export default Field;
