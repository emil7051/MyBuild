import { type ReactNode, useState } from 'react';
import { useDebouncedCallback } from 'use-debounce';
import Card from '@components/shared/Card';
import Field from '@components/shared/Field';
import { useTCOStore } from '@state/tcoStore';
import type { VehicleParamOverrides } from '@shared/types/tco.types';
import { vehicleParamOverridesSchema } from '@forms/wizardForm';
import { formatCurrency } from '@utils/format';

type FieldErrors = Partial<Record<keyof VehicleParamOverrides, string>>;

interface VehicleParamsFormProps {
  vehicleId?: string;
  title: string;
  showElectricFields?: boolean;
  subtitle?: ReactNode;
}

const VehicleParamsForm = ({
  vehicleId,
  title,
  showElectricFields = true,
  subtitle = 'Adjustments are optional - leave blank to use defaults.',
}: VehicleParamsFormProps) => {
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);
  const wizardData = useTCOStore((state) => state.wizardData);
  const updateWizard = useTCOStore((state) => state.updateWizard);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const clearFieldError = (fieldKey: keyof VehicleParamOverrides) => {
    setFieldErrors((prev) => {
      if (!prev[fieldKey]) return prev;
      const next = { ...prev };
      delete next[fieldKey];
      return next;
    });
  };

  const setFieldError = (fieldKey: keyof VehicleParamOverrides, message: string) => {
    setFieldErrors((prev) => ({ ...prev, [fieldKey]: message }));
  };

  const setOverrideImmediate = (patch: Partial<VehicleParamOverrides>) => {
    if (!vehicleId) {
      return;
    }

    // Get the field key being updated
    const fieldKey = Object.keys(patch)[0] as keyof VehicleParamOverrides;

    // Validate the patch before applying
    const result = vehicleParamOverridesSchema.partial().safeParse(patch);
    if (!result.success) {
      // Extract and display the error for this field
      const fieldError = result.error.flatten().fieldErrors[fieldKey];
      if (fieldError && fieldError.length > 0) {
        setFieldError(fieldKey, fieldError[0]);
      }
      return;
    }

    // Clear any existing error for this field
    clearFieldError(fieldKey);

    const existing = { ...(wizardData.vehicleParamOverrides ?? {}) };
    const current = { ...(existing[vehicleId] ?? {}) } as VehicleParamOverrides;

    Object.entries(result.data).forEach(([key, value]) => {
      if (value === undefined || value === null) {
        delete current[key as keyof VehicleParamOverrides];
      } else {
        current[key as keyof VehicleParamOverrides] = value as number;
      }
    });

    if (Object.keys(current).length === 0) {
      delete existing[vehicleId];
    } else {
      existing[vehicleId] = current;
    }

    updateWizard({ vehicleParamOverrides: existing });
  };

  const setOverride = useDebouncedCallback(setOverrideImmediate, 150);

  if (!vehicleId) {
    return (
      <Card title={title} subtitle="Select a truck to adjust its specifications.">
        <p className="text-sm text-slate-500">No truck selected yet.</p>
      </Card>
    );
  }

  const detail = vehicleDetails[vehicleId];
  const overrides = (wizardData.vehicleParamOverrides ?? {})[vehicleId] ?? {};

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

  const numberOrEmpty = (value?: number) => value ?? '';

  const hasOverrides = Object.keys(overrides).length > 0;

  const handleReset = () => {
    const existing = { ...(wizardData.vehicleParamOverrides ?? {}) };
    delete existing[vehicleId];
    updateWizard({ vehicleParamOverrides: existing });
  };

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
        <Field
          type="number"
          min={10000}
          max={2000000}
          label="Purchase price ($)"
          placeholder={formatCurrency(detail.msrp)}
          value={numberOrEmpty(overrides.msrp_override)}
          error={fieldErrors.msrp_override}
          onChange={(event) =>
            setOverride({
              msrp_override:
                event.currentTarget.value === '' ? undefined : Number(event.currentTarget.value),
            })
          }
        />
        <Field
          type="number"
          min={0.1}
          step="0.1"
          label="Payload capacity (tonnes)"
          placeholder={detail.payload.toFixed(1)}
          value={numberOrEmpty(overrides.payload_override)}
          error={fieldErrors.payload_override}
          onChange={(event) =>
            setOverride({
              payload_override:
                event.currentTarget.value === '' ? undefined : Number(event.currentTarget.value),
            })
          }
        />
        <Field
          type="number"
          min={0}
          label="Registration cost ($/year)"
          placeholder={formatCurrency(detail.annual_registration)}
          value={numberOrEmpty(overrides.annual_registration_override)}
          error={fieldErrors.annual_registration_override}
          onChange={(event) =>
            setOverride({
              annual_registration_override:
                event.currentTarget.value === '' ? undefined : Number(event.currentTarget.value),
            })
          }
        />
        <Field
          type="number"
          min={0}
          max={0.2}
          step="0.005"
          label="Interest rate"
          hint="Annual rate as a decimal - e.g. 0.06 for 6%."
          placeholder="0.06"
          value={numberOrEmpty(overrides.interest_rate_override)}
          error={fieldErrors.interest_rate_override}
          onChange={(event) =>
            setOverride({
              interest_rate_override:
                event.currentTarget.value === '' ? undefined : Number(event.currentTarget.value),
            })
          }
        />
        <Field
          type="number"
          min={50}
          max={2500}
          label="Range (kilometres)"
          placeholder={detail.range_km ? detail.range_km.toString() : 'N/A'}
          value={numberOrEmpty(overrides.range_km_override)}
          error={fieldErrors.range_km_override}
          onChange={(event) =>
            setOverride({
              range_km_override:
                event.currentTarget.value === '' ? undefined : Number(event.currentTarget.value),
            })
          }
        />
        {!isBev ? (
          <Field
            type="number"
            min={0.05}
            step="0.01"
            label="Fuel consumption (L/km)"
            placeholder={detail.litres_per_km.toFixed(2)}
            value={numberOrEmpty(overrides.litres_per_km_override)}
            error={fieldErrors.litres_per_km_override}
            onChange={(event) =>
              setOverride({
                litres_per_km_override:
                  event.currentTarget.value === '' ? undefined : Number(event.currentTarget.value),
              })
            }
          />
        ) : (
          <>
            <Field
              type="number"
              min={0}
              label="Battery size (kWh)"
              placeholder={detail.battery_capacity_kwh.toString()}
              value={numberOrEmpty(overrides.battery_capacity_kwh_override)}
              error={fieldErrors.battery_capacity_kwh_override}
              onChange={(event) =>
                setOverride({
                  battery_capacity_kwh_override:
                    event.currentTarget.value === ''
                      ? undefined
                      : Number(event.currentTarget.value),
                })
              }
            />
            <Field
              type="number"
              min={0.1}
              step="0.01"
              label="Energy use (kWh/km)"
              placeholder={detail.kwh_per_km.toString()}
              value={numberOrEmpty(overrides.kwh_per_km_override)}
              error={fieldErrors.kwh_per_km_override}
              onChange={(event) =>
                setOverride({
                  kwh_per_km_override:
                    event.currentTarget.value === ''
                      ? undefined
                      : Number(event.currentTarget.value),
                })
              }
            />
            <Field
              type="number"
              min={0.1}
              max={8}
              step="0.1"
              label="Charging time (hours)"
              hint="Custom charging duration for this truck."
              placeholder="1.5"
              value={numberOrEmpty(overrides.charging_time_hours_override)}
              error={fieldErrors.charging_time_hours_override}
              onChange={(event) =>
                setOverride({
                  charging_time_hours_override:
                    event.currentTarget.value === ''
                      ? undefined
                      : Number(event.currentTarget.value),
                })
              }
            />
          </>
        )}
      </div>
    </Card>
  );
};

export default VehicleParamsForm;
