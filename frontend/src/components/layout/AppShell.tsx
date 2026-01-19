import { NavLink } from 'react-router-dom';
import type { PropsWithChildren } from 'react';
import { toast } from 'react-hot-toast';
import { useTCOStore } from '@state/tcoStore';
import { useCalculationRunner } from '@hooks/useCalculations';
import { compactOverrides, compactVehicleParamOverrides } from '@utils/payload';
import type { ComparisonRequestPayload } from '@shared/types/tco.types';

const AppShell = ({ children }: PropsWithChildren) => {
  const wizardData = useTCOStore((state) => state.wizardData);
  const isCalculating = useTCOStore((state) => state.isCalculating);
  const { runComparison } = useCalculationRunner();

  const canCalculate = Boolean(wizardData.currentVehicle) && !isCalculating;

  const handleRunComparison = async () => {
    if (!wizardData.currentVehicle) {
      toast.error('Select a diesel truck first.');
      return;
    }

    const vehicleIds = Array.from(
      new Set([wizardData.currentVehicle, ...wizardData.comparisonVehicles.filter(Boolean)])
    );

    const payload: ComparisonRequestPayload = {
      vehicle_ids: vehicleIds,
      scenario_name: wizardData.scenario,
      purchase_method: wizardData.purchaseMethod,
      duty_cycle: wizardData.dutyCycle,
    };

    const overrides = compactOverrides(wizardData.overrides ?? {});
    if (Object.keys(overrides).length) {
      payload.overrides = overrides;
    }
    const vehicleOverrides = compactVehicleParamOverrides(
      wizardData.vehicleParamOverrides ?? {}
    );
    if (Object.keys(vehicleOverrides).length) {
      payload.vehicle_param_overrides = vehicleOverrides;
    }

    try {
      await runComparison(payload);
      toast.success('Comparison complete.');
    } catch (error) {
      console.error('Calculation failed', error);
      toast.error('Calculation failed. Please try again.');
    }
  };

  return (
  <div className="min-h-screen bg-brand-background text-brand-text font-body">
    <header className="bg-white text-black border-b-4 border-brand-primary shadow-sm relative z-10">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 sm:px-6 py-5">
        <div>
          <p className="text-xs font-bold opacity-80">Energy Futures Foundation</p>
          <h1 className="text-2xl font-heading font-normal tracking-tight">
            Truck Cost Calculator
          </h1>
        </div>
        <nav className="flex gap-1 text-sm font-semibold tracking-wide items-center">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `px-4 py-2 rounded-lg transition-all font-bold ${isActive
                ? 'bg-brand-primary text-black'
                : 'hover:bg-brand-primary/20'
              }`
            }
          >
            Configure
          </NavLink>
          <button
            onClick={() => void handleRunComparison()}
            disabled={!canCalculate}
            className={`px-4 py-2 rounded-lg transition-all font-bold ${
              canCalculate
                ? 'bg-brand-primary text-black hover:bg-brand-primary/80'
                : 'bg-brand-primary/40 text-black/50 cursor-not-allowed'
            }`}
          >
            {isCalculating ? 'Calculating...' : 'Run comparison'}
          </button>
          <NavLink
            to="/results"
            className={({ isActive }) =>
              `px-4 py-2 rounded-lg transition-all font-bold ${isActive
                ? 'bg-brand-primary text-black'
                : 'hover:bg-brand-primary/20'
              }`
            }
          >
            Results
          </NavLink>
        </nav>
      </div>
    </header>
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-4 sm:px-6 py-8 md:py-12">
      {children}
    </main>
  </div>
  );
};

export default AppShell;
