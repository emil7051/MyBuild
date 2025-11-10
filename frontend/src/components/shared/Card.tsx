import clsx from 'clsx';
import type { PropsWithChildren, ReactNode } from 'react';

interface CardProps {
  title?: string;
  subtitle?: ReactNode;
  headerAction?: ReactNode;
  className?: string;
}

const Card = ({ title, subtitle, headerAction, className, children }: PropsWithChildren<CardProps>) => (
  <section className={clsx('rounded-2xl border border-slate-100 bg-white p-6 shadow-sm', className)}>
    {(title || subtitle || headerAction) && (
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          {title && <h2 className="text-lg font-semibold text-slate-900">{title}</h2>}
          {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
        </div>
        {headerAction}
      </div>
    )}
    {children}
  </section>
);

export default Card;
