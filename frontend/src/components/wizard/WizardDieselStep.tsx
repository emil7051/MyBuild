import { useMemo } from 'react';
import Card from '@components/shared/Card';
import Select from '@components/shared/Select';
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
        title="Your current truck"
        subtitle="Select the diesel truck you operate today, or the closest match."
      >
        <Select
          label="Select your truck"
          value={wizardData.currentVehicle ?? ''}
          onChange={(event) => handleSelect(event.currentTarget.value)}
          hint="Showing diesel trucks only. Your selection is saved as you move through the steps."
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
        </Select>

        {selected ? (
          <div className="mt-8 rounded-lg border border-slate-200 bg-slate-50 p-6">
            <dl className="grid gap-6 md:grid-cols-2">
              <div className="border-b border-slate-200 pb-2 md:border-b-0 md:pb-0">
                <dt className="text-xs text-slate-500 font-bold mb-1">Model</dt>
                <dd className="text-lg font-heading font-bold text-slate-900">{selected.model_name}</dd>
              </div>
              <div className="border-b border-slate-200 pb-2 md:border-b-0 md:pb-0">
                <dt className="text-xs text-slate-500 font-bold mb-1">Weight class</dt>
                <dd className="text-lg font-heading font-bold text-slate-900">{selected.weight_class}</dd>
              </div>
              <div>
                <dt className="text-xs text-slate-500 font-bold mb-1">Payload</dt>
                <dd className="text-lg font-heading font-bold text-slate-900">{selected.payload.toFixed(1)} t</dd>
              </div>
              <div>
                <dt className="text-xs text-slate-500 font-bold mb-1">Purchase price</dt>
                <dd className="text-lg font-heading font-bold text-slate-900">{formatCurrency(selected.msrp)}</dd>
              </div>
            </dl>
          </div>
        ) : (
          <p className="mt-5 text-sm text-slate-500 italic">Select a truck above to see details.</p>
        )}
      </Card>

      <VehicleParamsForm
        vehicleId={wizardData.currentVehicle}
        title="Adjust specifications"
        showElectricFields={false}
        subtitle={null}
      />
    </div>
  );
};

export default WizardDieselStep;
