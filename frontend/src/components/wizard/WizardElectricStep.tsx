import { useEffect, useMemo, useState } from 'react';
import Card from '@components/shared/Card';
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
        title="Step 2 — Electric candidates"
        subtitle={
          baseline
            ? `Filtered to ${baseline.weight_class} BEVs so you can compare like-for-like.`
            : 'Select a diesel first to unlock the filtered BEV list.'
        }
      >
        {!baseline ? (
          <p className="text-sm text-slate-500">Choose a diesel in Step 1 first.</p>
        ) : (
          <>
            <label className="flex flex-col gap-2 text-sm font-medium text-slate-900">
              Add BEV alternative
              <select
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-base shadow-sm"
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
              </select>
              <span className="text-xs text-slate-500">
                You can add multiple BEVs — each will show up as a chip below.
              </span>
            </label>

            {suggestion && suggestionDetail && !wizardData.comparisonVehicles.includes(suggestion) && (
              <button
                type="button"
                className="mt-3 text-sm font-medium text-brand-600 underline"
                onClick={() => addComparator(suggestion)}
              >
                Add suggested pair: {suggestionDetail.model_name}
              </button>
            )}

            <div className="mt-6">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                Selected BEVs
              </p>
              {!wizardData.comparisonVehicles.length ? (
                <p className="mt-3 text-sm text-slate-500">No BEVs selected yet.</p>
              ) : (
                <div className="mt-3 flex flex-wrap gap-2">
                  {wizardData.comparisonVehicles.map((vehicleId) => {
                    const detail = vehicleDetails[vehicleId];
                    const isActive = vehicleId === activeComparison;
                    const displayName = detail?.model_name ?? vehicleId;
                    return (
                      <div
                        key={vehicleId}
                        className={`flex items-center gap-2 rounded-full border px-3 py-1 text-sm ${
                          isActive
                            ? 'border-brand-500 bg-brand-50 text-brand-700'
                            : 'border-slate-200 bg-white text-slate-600'
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
                        <span>{displayName}</span>
                        {detail && (
                          <span className="text-xs text-slate-400">
                            {formatCurrency(detail.msrp)}
                          </span>
                        )}
                        <button
                          type="button"
                          className="text-xs text-slate-400"
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
        title="BEV assumptions & overrides"
      />
    </div>
  );
};

export default WizardElectricStep;
