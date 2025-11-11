import type { ReactNode } from 'react';
import Card from '@components/shared/Card';
import Field from '@components/shared/Field';
import { useTCOStore } from '@state/tcoStore';
import type { VehicleParamOverrides } from '@shared/types/tco.types';
import { formatCurrency } from '@utils/format';

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
  subtitle = 'Overrides are optional — leave blank to use the catalog defaults.',
}: VehicleParamsFormProps) => {
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);
  const wizardData = useTCOStore((state) => state.wizardData);
  const updateWizard = useTCOStore((state) => state.updateWizard);

  const setOverride = (patch: Partial<VehicleParamOverrides>) => {
    if (!vehicleId) {
      return;
    }
    const existing = { ...(wizardData.vehicleParamOverrides ?? {}) };
    const current = { ...(existing[vehicleId] ?? {}) } as VehicleParamOverrides;

    Object.entries(patch).forEach(([key, value]) => {
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

  if (!vehicleId) {
    return (
      <Card title={title} subtitle="Select a vehicle to unlock parameter edits.">
        <p className="text-sm text-slate-500">No vehicle selected yet.</p>
      </Card>
    );
  }

  const detail = vehicleDetails[vehicleId];
  const overrides = (wizardData.vehicleParamOverrides ?? {})[vehicleId] ?? {};

  if (!detail) {
    return (
      <Card title={title} subtitle="Select a vehicle to edit its assumptions.">
        <p className="text-sm text-slate-500">
          Spec sheet missing for <span className="font-semibold">{vehicleId}</span>.
        </p>
      </Card>
    );
  }

  const isBev = detail.drivetrain_type === 'BEV' && showElectricFields;

  const numberOrEmpty = (value?: number) => (value ?? '');

  return (
    <Card title={title} subtitle={subtitle}>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-1">
        <Field
          type="number"
          min={10000}
          max={2000000}
          label="MSRP (A$)"
          placeholder={formatCurrency(detail.msrp)}
          value={numberOrEmpty(overrides.msrp_override)}
          onChange={(event) =>
            setOverride({
              msrp_override:
                event.currentTarget.value === ''
                  ? undefined
                  : Number(event.currentTarget.value),
            })
          }
        />
        <Field
          type="number"
          min={0.1}
          step="0.1"
          label="Payload (t)"
          placeholder={detail.payload.toFixed(1)}
          value={numberOrEmpty(overrides.payload_override)}
          onChange={(event) =>
            setOverride({
              payload_override:
                event.currentTarget.value === ''
                  ? undefined
                  : Number(event.currentTarget.value),
            })
          }
        />
        <Field
          type="number"
          min={0}
          label="Annual registration (A$)"
          placeholder={formatCurrency(detail.annual_registration)}
          value={numberOrEmpty(overrides.annual_registration_override)}
          onChange={(event) =>
            setOverride({
              annual_registration_override:
                event.currentTarget.value === ''
                  ? undefined
                  : Number(event.currentTarget.value),
            })
          }
        />
        <Field
          type="number"
          min={0}
          max={0.2}
          step="0.005"
          label="Financing interest rate"
          hint="Absolute annual rate — e.g. 0.06 for 6%."
          placeholder="0.06"
          value={numberOrEmpty(overrides.interest_rate_override)}
          onChange={(event) =>
            setOverride({
              interest_rate_override:
                event.currentTarget.value === ''
                  ? undefined
                  : Number(event.currentTarget.value),
            })
          }
        />
        <Field
          type="number"
          min={50}
          max={2500}
          label="Range (km)"
          placeholder={detail.range_km ? detail.range_km.toString() : 'N/A'}
          value={numberOrEmpty(overrides.range_km_override)}
          onChange={(event) =>
            setOverride({
              range_km_override:
                event.currentTarget.value === ''
                  ? undefined
                  : Number(event.currentTarget.value),
            })
          }
        />
        {!isBev ? (
          <Field
            type="number"
            min={0.05}
            step="0.01"
            label="Litres per km"
            placeholder={detail.litres_per_km.toFixed(2)}
            value={numberOrEmpty(overrides.litres_per_km_override)}
            onChange={(event) =>
              setOverride({
                litres_per_km_override:
                  event.currentTarget.value === ''
                    ? undefined
                    : Number(event.currentTarget.value),
              })
            }
          />
        ) : (
          <>
            <Field
              type="number"
              min={0}
              label="Battery capacity (kWh)"
              placeholder={detail.battery_capacity_kwh.toString()}
              value={numberOrEmpty(overrides.battery_capacity_kwh_override)}
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
              label="kWh per km"
              placeholder={detail.kwh_per_km.toString()}
              value={numberOrEmpty(overrides.kwh_per_km_override)}
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
              label="Charging Time (hours)"
              hint="Overrides the class-average charging duration."
              placeholder="1.5"
              value={numberOrEmpty(overrides.charging_time_hours_override)}
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
