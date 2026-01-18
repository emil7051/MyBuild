import type { InputHTMLAttributes } from 'react';
import clsx from 'clsx';

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  error?: string;
}

const Field = ({ label, hint, error, className, ...props }: FieldProps) => (
  <label className="flex h-full flex-col gap-2 text-sm text-slate-700 font-body">
    <span className="micro-heading text-black">{label}</span>
    <input
      className={clsx(
        'w-full border bg-white px-4 py-3 text-base text-black placeholder-slate-400 focus:outline-none transition-all rounded-lg shadow-sm',
        error
          ? 'border-rose-500 focus:border-rose-500 bg-rose-50'
          : 'border-slate-300 focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/25',
        className
      )}
      aria-invalid={Boolean(error)}
      {...props}
    />
    {error ? (
      <span className="block min-h-[1.25rem] text-xs font-semibold text-rose-600">{error}</span>
    ) : hint ? (
      <span className="block min-h-[1.25rem] text-xs text-slate-500">{hint}</span>
    ) : (
      <span className="block min-h-[1.25rem]" aria-hidden="true" />
    )}
  </label>
);

export default Field;
