import { useMemo } from 'react';
import { useFormContext, useWatch } from 'react-hook-form';
import clsx from 'clsx';
import Card from '@components/shared/Card';
import Field from '@components/shared/Field';
import type { WizardFormValues } from '@forms/wizardForm';
import { purchaseOptions, scenarioOptions } from '@forms/wizardForm';

const numberOrUndefined = (value: string) =>
  value === '' ? undefined : Number(value);

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
      title="Operating profile"
      subtitle="Scenarios and duty-cycle assumptions that drive the lifetime cost calculation."
    >
      <div className="grid gap-6 md:grid-cols-2">
        <label className="flex flex-col gap-2 text-sm font-medium text-slate-900">
          Scenario trajectory
          <select
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-base shadow-sm"
            {...register('scenario')}
          >
            {scenarioOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <span className="text-xs text-slate-500">
            {scenarioMeta
              ? scenarioMeta.description
              : 'Pulls trajectories from the pre-configured scenarios.'}
          </span>
        </label>

        <label className="flex flex-col gap-2 text-sm font-medium text-slate-900">
          Purchase method
          <select
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-base shadow-sm"
            {...register('purchaseMethod')}
          >
            {purchaseOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <span className="text-xs text-slate-500">Detemines pricing approach.</span>
        </label>
      </div>

      <div className="mt-5">
        <p className="text-sm font-semibold text-slate-900">Duty-cycle mix</p>
        <p className="text-xs text-slate-500">
          Percent of annual kilometres by route type. Must add up to 100%.
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <Field
            type="number"
            label="Urban (%)"
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
            label="Regional (%)"
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
            label="Long haul (%)"
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
          label="Annual kilometres"
          placeholder="23000"
          min={1000}
          hint="Override default kms for the selected vehicles."
          error={errors.overrides?.annual_kms_variation?.message}
          {...register('overrides.annual_kms_variation', {
            setValueAs: (value) => (value === '' ? undefined : Number(value)),
          })}
        />
        <Field
          type="number"
          label="Residual value multiplier"
          step="0.05"
          placeholder="1.0"
          hint="0.9 reduces resale expectations by 10%."
          error={errors.overrides?.residual_value_variation?.message}
          {...register('overrides.residual_value_variation', {
            setValueAs: (value) => (value === '' ? undefined : Number(value)),
          })}
        />
        <Field
          type="number"
          label="Maintenance multiplier"
          step="0.05"
          placeholder="1.0"
          hint="Increase/decrease maintenance costs globally."
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
