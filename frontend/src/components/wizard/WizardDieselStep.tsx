import { useMemo } from 'react';
import Card from '@components/shared/Card';
import { useVehicleCatalog } from '@hooks/useVehicleCatalog';
import { useTCOStore } from '@state/tcoStore';
import VehicleParamsForm from './VehicleParamsForm';
import { formatCurrency } from '@utils/format';

const WizardDieselStep = () => {
  const { data: catalog } = useVehicleCatalog();
  const wizardData = useTCOStore((state) => state.wizardData);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);
  const updateWizard = useTCOStore((state) => state.updateWizard);

  const dieselOptions = useMemo(
    () => (catalog ?? []).filter((vehicle) => vehicle.drivetrain_type === 'Diesel'),
    [catalog]
  );

  const selected = wizardData.currentVehicle
    ? vehicleDetails[wizardData.currentVehicle]
    : undefined;

  const handleSelect = (vehicleId: string) => {
    if (!vehicleId) {
      updateWizard({ currentVehicle: undefined, comparisonVehicles: [] });
      return;
    }
    const baseline = vehicleDetails[vehicleId];
    const filteredComparisons = wizardData.comparisonVehicles.filter((id) => {
      const detail = vehicleDetails[id];
      return detail && baseline && detail.weight_class === baseline.weight_class;
    });
    updateWizard({
      currentVehicle: vehicleId,
      comparisonVehicles: filteredComparisons,
    });
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(320px,380px)]">
      <Card
        title="Step 1 — Current diesel"
        subtitle="Pick the diesel you operate today."
      >
        <label className="flex flex-col gap-2 text-sm font-medium text-slate-900">
          Diesel model
          <select
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-base shadow-sm"
            value={wizardData.currentVehicle ?? ''}
            onChange={(event) => handleSelect(event.currentTarget.value)}
          >
            <option value="">Select…</option>
            {dieselOptions.map((vehicle) => (
              <option
                key={vehicle.vehicle_id}
                value={vehicle.vehicle_id}
                title={`${vehicle.model_name} (${vehicle.vehicle_id})`}
              >
                {vehicle.model_name} ({vehicle.weight_class})
              </option>
            ))}
          </select>
          <span className="text-xs text-slate-500">
            Filtered to diesel models only. Switching steps will keep your selection.
          </span>
        </label>

        {selected ? (
          <dl className="mt-6 grid gap-4 md:grid-cols-2">
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Model</dt>
              <dd className="text-base font-semibold text-slate-900">{selected.model_name}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Weight class</dt>
              <dd className="text-base font-semibold text-slate-900">{selected.weight_class}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">Payload</dt>
              <dd className="text-base font-semibold text-slate-900">{selected.payload.toFixed(1)} t</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-500">MSRP</dt>
              <dd className="text-base font-semibold text-slate-900">{formatCurrency(selected.msrp)}</dd>
            </div>
          </dl>
        ) : (
          <p className="mt-6 text-sm text-slate-500">Select a diesel to continue.</p>
        )}
      </Card>

      <VehicleParamsForm
        vehicleId={wizardData.currentVehicle}
        title="Diesel assumptions & overrides"
        showElectricFields={false}
        subtitle={null}
      />
    </div>
  );
};

export default WizardDieselStep;
