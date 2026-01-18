import { useFormContext } from 'react-hook-form';
import Card from '@components/shared/Card';
import Field from '@components/shared/Field';
import type { WizardFormValues } from '@forms/wizardForm';

const WizardCostStep = () => {
  const {
    register,
    formState: { errors },
  } = useFormContext<WizardFormValues>();

  return (
    <Card title="Price adjustments" subtitle="Optional adjustments for quick scenario exploration.">
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2 md:gap-6">
          <Field
            type="number"
            label="Diesel price adjustment"
            step="0.05"
            placeholder="1.00"
            hint="Enter 1.10 for 10% higher prices, 0.90 for 10% lower."
            error={errors.overrides?.fuel_price_variation?.message}
            {...register('overrides.fuel_price_variation', {
              setValueAs: (value) => (value === '' ? undefined : Number(value)),
            })}
          />
          <Field
            type="number"
            label="Electricity price adjustment"
            step="0.05"
            placeholder="1.00"
            hint="Enter 1.10 for 10% higher prices, 0.90 for 10% lower."
            error={errors.overrides?.electricity_price_variation?.message}
            {...register('overrides.electricity_price_variation', {
              setValueAs: (value) => (value === '' ? undefined : Number(value)),
            })}
          />
        </div>
        <div className="grid gap-4 md:grid-cols-2 md:gap-6">
          <Field
            type="number"
            label="Battery life adjustment"
            step="0.05"
            placeholder="1.00"
            hint="Enter 0.70 for shorter battery life (higher replacement cost), 1.20 for longer life."
            error={errors.overrides?.battery_life_variation?.message}
            {...register('overrides.battery_life_variation', {
              setValueAs: (value) => (value === '' ? undefined : Number(value)),
            })}
          />
          <Field
            type="number"
            label="Charging efficiency adjustment"
            step="0.05"
            placeholder="1.00"
            hint="Affects energy required per kilometre for electric trucks."
            error={errors.overrides?.charging_efficiency_variation?.message}
            {...register('overrides.charging_efficiency_variation', {
              setValueAs: (value) => (value === '' ? undefined : Number(value)),
            })}
          />
        </div>
      </div>
    </Card>
  );
};

export default WizardCostStep;
