import type { SelectHTMLAttributes } from 'react';
import clsx from 'clsx';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
    label?: string;
    hint?: string;
    error?: string;
}

const Select = ({ label, hint, error, className, children, ...props }: SelectProps) => (
    <label className="flex flex-col gap-2 text-sm text-slate-700 font-body w-full">
        {label && <span className="micro-heading text-black">{label}</span>}
        <div className="relative">
            <select
                className={clsx(
                    'w-full appearance-none border bg-white px-4 py-3.5 pr-10 text-base text-black placeholder-slate-400 focus:outline-none transition-all rounded-lg shadow-sm',
                    error
                        ? 'border-rose-500 focus:border-rose-500 bg-rose-50'
                        : 'border-slate-300 focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/25',
                    className
                )}
                aria-invalid={Boolean(error)}
                {...props}
            >
                {children}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-500">
                <svg className="h-4 w-4 fill-current" viewBox="0 0 20 20">
                    <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" fillRule="evenodd" />
                </svg>
            </div>
        </div>
        {error ? (
            <span className="block min-h-[1.25rem] text-xs font-semibold text-rose-600">{error}</span>
        ) : hint ? (
            <span className="block min-h-[1.25rem] text-xs text-slate-500">{hint}</span>
        ) : (
            <span className="block min-h-[1.25rem]" aria-hidden="true" />
        )}
    </label>
);

export default Select;
