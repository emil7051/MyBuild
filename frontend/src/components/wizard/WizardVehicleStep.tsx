import Card from '@components/shared/Card';
import Button from '@components/shared/Button';
import { useVehicleCatalog } from '@hooks/useVehicleCatalog';
import { useTCOStore } from '@state/tcoStore';
import { formatCurrency } from '@utils/format';

const WizardVehicleStep = () => {
  const { data: vehicles } = useVehicleCatalog();
  const wizardData = useTCOStore((state) => state.wizardData);
  const currentVehicle = wizardData.currentVehicle;
  const comparisonVehicles = wizardData.comparisonVehicles;
  const updateWizard = useTCOStore((state) => state.updateWizard);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);

  const handlePrimarySelect = (vehicleId: string) => {
    updateWizard({ currentVehicle: vehicleId });
  };

  const toggleComparison = (vehicleId: string) => {
    const exists = comparisonVehicles.includes(vehicleId);
    const updated = exists
      ? comparisonVehicles.filter((id) => id !== vehicleId)
      : [...comparisonVehicles, vehicleId];
    updateWizard({ comparisonVehicles: updated });
  };

  return (
    <Card
      title="Vehicle selection"
      subtitle="Choose a baseline and optional comparators. Specs load instantly from the shared catalog."
    >
      {!vehicles?.length ? (
        <p className="text-sm text-slate-500">Vehicle catalog not available.</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {vehicles.map((vehicle) => {
            const isPrimary = currentVehicle === vehicle.vehicle_id;
            const isComparison = comparisonVehicles.includes(vehicle.vehicle_id);
            const detail = vehicleDetails[vehicle.vehicle_id];

            return (
              <article
                key={vehicle.vehicle_id}
                className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
                      {vehicle.weight_class}
                    </p>
                    <h3 className="text-lg font-semibold text-slate-900">{vehicle.model_name}</h3>
                    <p className="text-sm text-slate-500">{vehicle.drivetrain_type}</p>
                  </div>
                  {isPrimary && (
                    <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-600">
                      Baseline
                    </span>
                  )}
                </div>
                <div className="mt-4 flex gap-2">
                  <Button
                    variant={isPrimary ? 'secondary' : 'primary'}
                    className="flex-1"
                    onClick={() => handlePrimarySelect(vehicle.vehicle_id)}
                  >
                    {isPrimary ? 'Selected' : 'Set baseline'}
                  </Button>
                  <Button
                    variant={isComparison ? 'secondary' : 'ghost'}
                    className="flex-1"
                    onClick={() => toggleComparison(vehicle.vehicle_id)}
                  >
                    {isComparison ? 'Remove compare' : 'Add compare'}
                  </Button>
                </div>
                {detail ? (
                  <dl className="mt-4 grid grid-cols-2 gap-3 text-xs text-slate-500">
                    <div>
                      <dt className="uppercase tracking-wide">Payload</dt>
                      <dd className="text-base font-semibold text-slate-900">
                        {detail.payload.toFixed(1)} t
                      </dd>
                    </div>
                    <div>
                      <dt className="uppercase tracking-wide">Range</dt>
                      <dd className="text-base font-semibold text-slate-900">
                        {detail.range_km.toLocaleString()} km
                      </dd>
                    </div>
                    <div>
                      <dt className="uppercase tracking-wide">Battery / Tank</dt>
                      <dd className="text-base font-semibold text-slate-900">
                        {detail.drivetrain_type === 'BEV'
                          ? `${detail.battery_capacity_kwh.toLocaleString()} kWh`
                          : `${detail.litres_per_km.toFixed(2)} L/km`}
                      </dd>
                    </div>
                    <div>
                      <dt className="uppercase tracking-wide">MSRP</dt>
                      <dd className="text-base font-semibold text-slate-900">
                        {formatCurrency(detail.msrp)}
                      </dd>
                    </div>
                  </dl>
                ) : (
                  <p className="mt-4 text-xs text-slate-400">Specs unavailable for this vehicle.</p>
                )}
              </article>
            );
          })}
        </div>
      )}
    </Card>
  );
};

export default WizardVehicleStep;
