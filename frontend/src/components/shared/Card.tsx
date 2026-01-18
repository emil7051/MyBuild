import clsx from 'clsx';
import type { PropsWithChildren, ReactNode } from 'react';

interface CardProps {
  title?: string;
  subtitle?: ReactNode;
  headerAction?: ReactNode;
  className?: string;
}

const Card = ({ title, subtitle, headerAction, className, children }: PropsWithChildren<CardProps>) => (
  <section className={clsx(
    'bg-white p-4 sm:p-6 md:p-8 border border-slate-200 rounded-lg shadow-card hover:shadow-card-hover border-l-4 border-l-brand-primary transition-shadow',
    className
  )}>
    {(title || subtitle || headerAction) && (
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          {title && <h2 className="text-2xl font-heading font-normal text-black tracking-tight">{title}</h2>}
          {subtitle && <p className="text-sm text-slate-600 mt-1">{subtitle}</p>}
        </div>
        {headerAction}
      </div>
    )}
    {children}
  </section>
);

export default Card;
