import { useEffect, useMemo, useState } from 'react';
import Card from '@components/shared/Card';
import Select from '@components/shared/Select';
import { useVehicleCatalog } from '@hooks/useVehicleCatalog';
import { useTCOStore } from '@state/tcoStore';
import VehicleParamsForm from './VehicleParamsForm';
import { formatCurrency } from '@utils/format';

const WizardElectricStep = () => {
  const { data: catalog } = useVehicleCatalog();
  const wizardData = useTCOStore((state) => state.wizardData);
  const updateWizard = useTCOStore((state) => state.updateWizard);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);
  const [activeComparison, setActiveComparison] = useState<string | undefined>(
    () => wizardData.comparisonVehicles[0]
  );

  const baseline = wizardData.currentVehicle
    ? vehicleDetails[wizardData.currentVehicle]
    : undefined;

  const bevOptions = useMemo(() => {
    if (!baseline) {
      return [];
    }
    return (catalog ?? []).filter(
      (vehicle) =>
        vehicle.drivetrain_type === 'BEV' && vehicle.weight_class === baseline.weight_class
    );
  }, [baseline, catalog]);

  useEffect(() => {
    if (!wizardData.comparisonVehicles.length) {
      setActiveComparison(undefined);
      return;
    }
    if (!activeComparison || !wizardData.comparisonVehicles.includes(activeComparison)) {
      setActiveComparison(wizardData.comparisonVehicles[0]);
    }
  }, [activeComparison, wizardData.comparisonVehicles]);

  const addComparator = (vehicleId: string) => {
    if (!vehicleId) {
      return;
    }
    const deduped = Array.from(
      new Set([...wizardData.comparisonVehicles, vehicleId])
    );
    updateWizard({ comparisonVehicles: deduped });
    setActiveComparison(vehicleId);
  };

  const removeComparator = (vehicleId: string) => {
    updateWizard({
      comparisonVehicles: wizardData.comparisonVehicles.filter((id) => id !== vehicleId),
    });
  };

  const suggestion =
    baseline?.comparison_pair && baseline.comparison_pair.startsWith('BEV')
      ? baseline.comparison_pair
      : undefined;
  const suggestionDetail = suggestion ? vehicleDetails[suggestion] : undefined;

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(320px,380px)]">
      <Card
        title="Electric trucks to compare"
        subtitle={
          baseline
            ? `Showing ${baseline.weight_class} electric trucks so you can compare like-for-like.`
            : 'Select a diesel truck first to see available electric options.'
        }
      >
        {!baseline ? (
          <p className="text-sm text-slate-500">Choose a diesel truck in step 1 first.</p>
        ) : (
          <>
            <Select
              label="Add an electric truck"
              hint="You can add multiple electric trucks - each will show up as a chip below."
              defaultValue=""
              onChange={(event) => {
                const id = event.currentTarget.value;
                if (id) {
                  addComparator(id);
                  event.currentTarget.value = '';
                }
              }}
            >
              <option value="">Select…</option>
              {bevOptions.map((vehicle) => (
                <option
                  key={vehicle.vehicle_id}
                  value={vehicle.vehicle_id}
                  title={`${vehicle.model_name} (${vehicle.vehicle_id})`}
                >
                  {vehicle.model_name}
                </option>
              ))}
            </Select>

            {suggestion && suggestionDetail && !wizardData.comparisonVehicles.includes(suggestion) && (
              <button
                type="button"
                className="mt-3 text-sm font-medium text-brand-blue hover:underline"
                onClick={() => addComparator(suggestion)}
              >
                + Add suggested pair: {suggestionDetail.model_name}
              </button>
            )}

            <div className="mt-8">
              <p className="text-xs font-bold text-slate-500 mb-3">
                Trucks you're comparing
              </p>
              {!wizardData.comparisonVehicles.length ? (
                <p className="text-sm text-slate-400 italic">No electric trucks selected yet.</p>
              ) : (
                <div className="flex flex-wrap gap-3">
                  {wizardData.comparisonVehicles.map((vehicleId) => {
                    const detail = vehicleDetails[vehicleId];
                    const isActive = vehicleId === activeComparison;
                    const displayName = detail?.model_name ?? vehicleId;
                    return (
                      <div
                        key={vehicleId}
                        className={`flex items-center gap-3 rounded-md border px-4 py-2 text-sm transition-all shadow-sm cursor-pointer ${isActive
                          ? 'border-brand-primary bg-brand-primary/10 text-black shadow-md ring-1 ring-brand-primary'
                          : 'border-slate-200 bg-white text-slate-600 hover:border-brand-primary/50'
                          }`}
                        role="button"
                        tabIndex={0}
                        onClick={() => setActiveComparison(vehicleId)}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter' || event.key === ' ') {
                            event.preventDefault();
                            setActiveComparison(vehicleId);
                          }
                        }}
                      >
                        <div className="flex flex-col">
                          <span className="font-bold leading-tight">{displayName}</span>
                          {detail && (
                            <span className="text-xs text-slate-500">
                              {formatCurrency(detail.msrp)}
                            </span>
                          )}
                        </div>
                        <button
                          type="button"
                          className="flex h-5 w-5 items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-rose-100 hover:text-rose-600 transition-colors"
                          aria-label={`Remove ${displayName}`}
                          onClick={(event) => {
                            event.stopPropagation();
                            removeComparator(vehicleId);
                          }}
                        >
                          ×
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        )}
      </Card>

      <VehicleParamsForm
        vehicleId={activeComparison}
        title="Adjust specifications"
      />
    </div>
  );
};

export default WizardElectricStep;
