import { useMemo } from 'react';
import { useFormContext, useWatch } from 'react-hook-form';
import clsx from 'clsx';
import Card from '@components/shared/Card';
import Field from '@components/shared/Field';
import Select from '@components/shared/Select';
import type { WizardFormValues } from '@forms/wizardForm';
import { purchaseOptions, scenarioOptions } from '@forms/wizardForm';

const numberOrUndefined = (value: unknown): number | undefined => {
  if (value === '' || value === undefined || value === null) return undefined;
  const num = Number(value);
  return Number.isNaN(num) ? undefined : num;
};

const WizardOperatingStep = () => {
  const {
    register,
    watch,
    control,
    formState: { errors },
  } = useFormContext<WizardFormValues>();
  const scenario = watch('scenario');
  const scenarioMeta = scenarioOptions.find((option) => option.value === scenario);

  // Real-time duty cycle validation
  const dutyCycle = useWatch({ control, name: 'dutyCycle' });
  const dutyCycleSum = useMemo(() => {
    const { urban = 0, regional = 0, longHaul = 0 } = dutyCycle || {};
    return (Number(urban) || 0) + (Number(regional) || 0) + (Number(longHaul) || 0);
  }, [dutyCycle]);
  const isDutyCycleValid = Math.abs(dutyCycleSum - 100) < 0.01;

  return (
    <Card
      title="How you use your trucks"
      subtitle="Settings that affect your lifetime cost calculation."
    >
      <div className="grid gap-6 md:grid-cols-2">
        <Select
          label="Market scenario"
          hint={
            scenarioMeta
              ? scenarioMeta.description
              : 'Choose a scenario to see how costs might change over time.'
          }
          {...register('scenario')}
        >
          {scenarioOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>

        <Select
          label="How will you buy?"
          hint="Determines pricing approach."
          {...register('purchaseMethod')}
        >
          {purchaseOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      </div>

      <div className="mt-5">
        <p className="text-sm font-semibold text-slate-900">Your typical routes</p>
        <p className="text-xs text-slate-500">
          Percent of annual kilometres by route type. Must add up to 100%.
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <Field
            type="number"
            label="City/metro (%)"
            placeholder="60"
            min={0}
            max={100}
            error={errors.dutyCycle?.urban?.message}
            {...register('dutyCycle.urban', {
              setValueAs: numberOrUndefined,
            })}
          />
          <Field
            type="number"
            label="Regional roads (%)"
            placeholder="25"
            min={0}
            max={100}
            error={errors.dutyCycle?.regional?.message}
            {...register('dutyCycle.regional', {
              setValueAs: numberOrUndefined,
            })}
          />
          <Field
            type="number"
            label="Highway/long distance (%)"
            placeholder="15"
            min={0}
            max={100}
            error={errors.dutyCycle?.longHaul?.message}
            {...register('dutyCycle.longHaul', {
              setValueAs: numberOrUndefined,
            })}
          />
        </div>
        <div
          className={clsx(
            'mt-3 text-sm font-medium',
            isDutyCycleValid ? 'text-green-600' : 'text-red-600'
          )}
        >
          Total: {dutyCycleSum.toFixed(0)}%
          {!isDutyCycleValid && (
            <span className="ml-2 text-xs font-normal">(Must equal 100%)</span>
          )}
        </div>
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <Field
          type="number"
          label="Kilometres per year"
          placeholder="23000"
          min={1000}
          hint="Custom annual distance for your trucks."
          error={errors.overrides?.annual_kms_variation?.message}
          {...register('overrides.annual_kms_variation', {
            setValueAs: (value) => (value === '' ? undefined : Number(value)),
          })}
        />
        <Field
          type="number"
          label="Resale value adjustment"
          step="0.05"
          placeholder="1.0"
          hint="Enter 0.90 for 10% lower resale, 1.10 for 10% higher."
          error={errors.overrides?.residual_value_variation?.message}
          {...register('overrides.residual_value_variation', {
            setValueAs: (value) => (value === '' ? undefined : Number(value)),
          })}
        />
        <Field
          type="number"
          label="Maintenance cost adjustment"
          step="0.05"
          placeholder="1.0"
          hint="Enter 1.10 for 10% higher costs, 0.90 for 10% lower."
          error={errors.overrides?.maintenance_cost_variation?.message}
          {...register('overrides.maintenance_cost_variation', {
            setValueAs: (value) => (value === '' ? undefined : Number(value)),
          })}
        />
      </div>
    </Card>
  );
};

export default WizardOperatingStep;
