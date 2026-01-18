import clsx from 'clsx';

export interface WizardStep {
  title: string;
  description: string;
}

interface WizardStepperProps {
  steps: WizardStep[];
  activeIndex: number;
  onStepClick?: (index: number) => void;
}

const WizardStepper = ({ steps, activeIndex, onStepClick }: WizardStepperProps) => (
  <ol className="flex flex-col gap-4 md:flex-row md:items-stretch md:gap-6">
    {steps.map((step, index) => {
      const isActive = index === activeIndex;
      const isPast = index < activeIndex;

      return (
        <li
          key={step.title}
          className={clsx(
            'flex-1 relative pl-4 py-3 min-h-[48px] border-l-4 rounded-r-lg transition-all duration-300 ease-in-out group',
            isActive
              ? 'border-brand-primary bg-brand-primary/10'
              : isPast
                ? 'border-black cursor-pointer hover:border-brand-primary/60 hover:bg-slate-50'
                : 'border-slate-200'
          )}
          role={onStepClick ? 'button' : undefined}
          tabIndex={onStepClick ? 0 : -1}
          aria-current={isActive}
          onClick={() => onStepClick?.(index)}
          onKeyDown={(event) => {
            if (!onStepClick) {
              return;
            }
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              onStepClick(index);
            }
          }}
        >
          <div className="flex flex-col h-full justify-between">
            <div>
              <span className={clsx(
                "text-xs font-bold block mb-1",
                isActive ? "text-brand-primary" : isPast ? "text-slate-500 group-hover:text-slate-700" : "text-slate-300"
              )}>
                Step {index + 1}
              </span>
              <p className={clsx(
                "text-lg font-heading font-bold leading-none",
                isActive ? "text-black" : isPast ? "text-slate-600 group-hover:text-black" : "text-slate-300"
              )}>{step.title}</p>
            </div>
          </div>
        </li>
      );
    })}
  </ol>
);

export default WizardStepper;
