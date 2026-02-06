import { type ComponentProps, type ReactNode } from 'react';
import { Controller, useFormContext, useWatch } from 'react-hook-form';
import Card from '@components/shared/Card';
import Field from '@components/shared/Field';
import type { WizardFormValues } from '@forms/wizardForm';
import { useTCOStore } from '@state/tcoStore';
import type { VehicleParamOverrides } from '@shared/types/tco.types';
import { formatCurrency } from '@utils/format';

interface VehicleParamsFormProps {
  vehicleId?: string;
  title: string;
  showElectricFields?: boolean;
  subtitle?: ReactNode;
}

type NumberOverrideFieldProps = Omit<
  ComponentProps<typeof Field>,
  'type' | 'value' | 'error' | 'onChange' | 'name' | 'ref'
>;

const toOptionalNumber = (value: string): number | undefined => {
  if (value === '') {
    return undefined;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
};

const VehicleParamsForm = ({
  vehicleId,
  title,
  showElectricFields = true,
  subtitle = 'Adjustments are optional - leave blank to use defaults.',
}: VehicleParamsFormProps) => {
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);
  const { control, clearErrors, getValues, setValue } = useFormContext<WizardFormValues>();
  const allVehicleOverrides = useWatch({ control, name: 'vehicleParamOverrides' }) ?? {};

  if (!vehicleId) {
    return (
      <Card title={title} subtitle="Select a truck to adjust its specifications.">
        <p className="text-sm text-slate-500">No truck selected yet.</p>
      </Card>
    );
  }

  const detail = vehicleDetails[vehicleId];
  if (!detail) {
    return (
      <Card title={title} subtitle="Select a truck to adjust its specifications.">
        <p className="text-sm text-slate-500">
          Details missing for <span className="font-semibold">{vehicleId}</span>.
        </p>
      </Card>
    );
  }

  const isBev = detail.drivetrain_type === 'BEV' && showElectricFields;
  const overrides = allVehicleOverrides[vehicleId] ?? {};
  const hasOverrides = Object.values(overrides).some((value) => value !== undefined && value !== null);

  const handleReset = () => {
    const existing = { ...(getValues('vehicleParamOverrides') ?? {}) };
    delete existing[vehicleId];
    setValue('vehicleParamOverrides', existing, {
      shouldDirty: true,
      shouldTouch: true,
      shouldValidate: true,
    });
    clearErrors('vehicleParamOverrides');
  };

  const renderNumberField = (
    fieldKey: keyof VehicleParamOverrides,
    fieldProps: NumberOverrideFieldProps
  ) => (
    <Controller
      key={fieldKey}
      control={control}
      name={`vehicleParamOverrides.${vehicleId}.${fieldKey}` as const}
      render={({ field, fieldState }) => (
        <Field
          {...fieldProps}
          type="number"
          value={field.value ?? ''}
          error={fieldState.error?.message}
          onChange={(event) => field.onChange(toOptionalNumber(event.currentTarget.value))}
          onBlur={field.onBlur}
          name={field.name}
          ref={field.ref}
        />
      )}
    />
  );

  return (
    <Card
      title={title}
      subtitle={subtitle}
      headerAction={
        hasOverrides && (
          <button
            onClick={handleReset}
            className="text-xs font-bold text-rose-600 hover:text-rose-700 hover:underline"
            title="Reset all overrides to default values"
          >
            Reset to defaults
          </button>
        )
      }
    >
      <div className="grid gap-x-6 gap-y-6 sm:grid-cols-2">
        {renderNumberField('msrp_override', {
          label: 'Purchase price ($)',
          min: 10000,
          max: 2000000,
          placeholder: formatCurrency(detail.msrp),
        })}
        {renderNumberField('payload_override', {
          label: 'Payload capacity (tonnes)',
          min: 0.1,
          step: '0.1',
          placeholder: detail.payload.toFixed(1),
        })}
        {renderNumberField('annual_registration_override', {
          label: 'Registration cost ($/year)',
          min: 0,
          placeholder: formatCurrency(detail.annual_registration),
        })}
        {renderNumberField('interest_rate_override', {
          label: 'Interest rate',
          min: 0,
          max: 0.2,
          step: '0.005',
          hint: 'Annual rate as a decimal - e.g. 0.06 for 6%.',
          placeholder: '0.06',
        })}
        {renderNumberField('range_km_override', {
          label: 'Range (kilometres)',
          min: 50,
          max: 2500,
          placeholder: detail.range_km ? detail.range_km.toString() : 'N/A',
        })}
        {!isBev ? (
          renderNumberField('litres_per_km_override', {
            label: 'Fuel consumption (L/km)',
            min: 0.05,
            step: '0.01',
            placeholder: detail.litres_per_km.toFixed(2),
          })
        ) : (
          <>
            {renderNumberField('battery_capacity_kwh_override', {
              label: 'Battery size (kWh)',
              min: 0,
              placeholder: detail.battery_capacity_kwh.toString(),
            })}
            {renderNumberField('kwh_per_km_override', {
              label: 'Energy use (kWh/km)',
              min: 0.1,
              step: '0.01',
              placeholder: detail.kwh_per_km.toString(),
            })}
            {renderNumberField('charging_time_hours_override', {
              label: 'Charging time (hours)',
              min: 0.1,
              max: 8,
              step: '0.1',
              hint: 'Custom charging duration for this truck.',
              placeholder: '1.5',
            })}
          </>
        )}
      </div>
    </Card>
  );
};

export default VehicleParamsForm;
