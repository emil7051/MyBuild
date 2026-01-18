import type { ButtonHTMLAttributes, PropsWithChildren } from 'react';
import clsx from 'clsx';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
}

const variantStyles: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary: 'bg-brand-primary text-brand-secondary hover:bg-[#E6B300] border-2 border-transparent shadow-button',
  secondary: 'bg-transparent text-black border-2 border-black hover:bg-black hover:text-white',
  ghost: 'bg-transparent text-slate-600 hover:text-black hover:bg-black/5',
};

const Button = ({ children, className, variant = 'primary', ...props }: PropsWithChildren<ButtonProps>) => (
  <button
    className={clsx(
      'inline-flex items-center justify-center px-6 py-3 text-sm font-bold transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 rounded-lg active:scale-[0.98]',
      variantStyles[variant],
      className
    )}
    {...props}
  >
    {children}
  </button>
);

export default Button;
