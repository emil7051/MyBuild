import clsx from 'clsx';

export interface WizardStep {
  title: string;
  description: string;
}

interface WizardStepperProps {
  steps: WizardStep[];
  activeIndex: number;
}

const WizardStepper = ({ steps, activeIndex }: WizardStepperProps) => (
  <ol className="flex flex-col gap-4 md:flex-row md:items-stretch md:gap-6">
    {steps.map((step, index) => (
      <li
        key={step.title}
        className={clsx(
          'flex-1 rounded-2xl border px-4 py-3 shadow-sm transition-colors',
          index === activeIndex
            ? 'border-brand-200 bg-white'
            : 'border-transparent bg-slate-100 text-slate-500'
        )}
      >
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          Step {index + 1}
        </p>
        <p className="text-base font-semibold text-slate-900">{step.title}</p>
        <p className="text-sm text-slate-500">{step.description}</p>
      </li>
    ))}
  </ol>
);

export default WizardStepper;
