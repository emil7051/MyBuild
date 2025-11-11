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
    <Card title="Cost sensitivity" subtitle="Optional multipliers for quick scenario exploration.">
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2 md:gap-6">
          <Field
            type="number"
            label="Diesel $ multiplier"
            step="0.05"
            placeholder="1.00"
            hint="1.12 represents a 12% diesel price increase across the life of the vehicle."
            error={errors.overrides?.fuel_price_variation?.message}
            {...register('overrides.fuel_price_variation', {
              setValueAs: (value) => (value === '' ? undefined : Number(value)),
            })}
          />
          <Field
            type="number"
            label="Electricity $ multiplier"
            step="0.05"
            placeholder="1.00"
            hint="Apply shocks or savings to the energy price trajectory."
            error={errors.overrides?.electricity_price_variation?.message}
            {...register('overrides.electricity_price_variation', {
              setValueAs: (value) => (value === '' ? undefined : Number(value)),
            })}
          />
        </div>
        <div className="grid gap-4 md:grid-cols-2 md:gap-6">
          <Field
            type="number"
            label="Battery multiplier"
            step="0.05"
            placeholder="1.00"
            hint="0.7 shortens life (higher replacement cost), 1.2 extends it."
            error={errors.overrides?.battery_life_variation?.message}
            {...register('overrides.battery_life_variation', {
              setValueAs: (value) => (value === '' ? undefined : Number(value)),
            })}
          />
          <Field
            type="number"
            label="Charging efficiency multiplier"
            step="0.05"
            placeholder="1.00"
            hint="Impacts BEV charging energy required per kilometre."
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
