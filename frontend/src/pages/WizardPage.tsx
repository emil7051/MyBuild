import { useEffect } from 'react';
import { FormProvider, type FieldPath, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Card from '@components/shared/Card';
import Button from '@components/shared/Button';
import WizardCostStep from '@components/wizard/WizardCostStep';
import WizardOperatingStep from '@components/wizard/WizardOperatingStep';
import WizardVehicleStep from '@components/wizard/WizardVehicleStep';
import SelectedVehiclesSummary from '@components/wizard/SelectedVehiclesSummary';
import WizardStepper, { type WizardStep } from '@components/wizard/WizardStepper';
import { useCalculationRunner } from '@hooks/useCalculations';
import { useTCOStore } from '@state/tcoStore';
import { compactOverrides } from '@utils/payload';
import type { ComparisonRequestPayload, DutyCycle } from '@shared/types/tco.types';
import type { WizardFormValues } from '@forms/wizardForm';
import { wizardFormSchema } from '@forms/wizardForm';
import { toast } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

const steps: WizardStep[] = [
  {
    title: 'Vehicle selection',
    description: 'Choose the current truck and optional comparators.',
  },
  {
    title: 'Operating profile',
    description: 'Define scenario, kms, and purchase assumptions.',
  },
  {
    title: 'Cost inputs',
    description: 'Apply optional multipliers for stress testing.',
  },
];

const stepFieldMap: FieldPath<WizardFormValues>[][] = [
  [],
  [
    'scenario',
    'purchaseMethod',
    'dutyCycle.urban',
    'dutyCycle.regional',
    'dutyCycle.longHaul',
    'overrides.annual_kms_variation',
    'overrides.residual_value_variation',
    'overrides.maintenance_cost_variation',
  ],
  [
    'overrides.fuel_price_variation',
    'overrides.electricity_price_variation',
    'overrides.battery_life_variation',
    'overrides.charging_efficiency_variation',
  ],
];

const WizardPage = () => {
  const navigate = useNavigate();
  const stepIndex = useTCOStore((state) => state.stepIndex);
  const setStepIndex = useTCOStore((state) => state.setStepIndex);
  const wizardData = useTCOStore((state) => state.wizardData);
  const isCalculating = useTCOStore((state) => state.isCalculating);
  const updateWizard = useTCOStore((state) => state.updateWizard);
  const { runComparison } = useCalculationRunner();
  const formMethods = useForm<WizardFormValues>({
    resolver: zodResolver(wizardFormSchema),
    mode: 'onTouched',
    defaultValues: {
      scenario: wizardData.scenario,
      purchaseMethod: wizardData.purchaseMethod,
      dutyCycle: wizardData.dutyCycle,
      overrides: wizardData.overrides ?? {},
    },
  });

  const isLastStep = stepIndex === steps.length - 1;
  const baselineSelected = Boolean(wizardData.currentVehicle);
  const stepComponents = [
    <WizardVehicleStep key="vehicles" />,
    <WizardOperatingStep key="operating" />,
    <WizardCostStep key="cost" />,
  ];
  const activeComponent = stepComponents[stepIndex];

  useEffect(() => {
    const currentValues = formMethods.getValues();
    const overridesMatch =
      JSON.stringify(currentValues.overrides ?? {}) === JSON.stringify(wizardData.overrides ?? {});
    const dutyCycleMatch =
      currentValues.dutyCycle?.urban === wizardData.dutyCycle.urban &&
      currentValues.dutyCycle?.regional === wizardData.dutyCycle.regional &&
      currentValues.dutyCycle?.longHaul === wizardData.dutyCycle.longHaul;
    if (
      currentValues.scenario !== wizardData.scenario ||
      currentValues.purchaseMethod !== wizardData.purchaseMethod ||
      !overridesMatch ||
      !dutyCycleMatch
    ) {
      formMethods.reset({
        scenario: wizardData.scenario,
        purchaseMethod: wizardData.purchaseMethod,
        dutyCycle: wizardData.dutyCycle,
        overrides: wizardData.overrides ?? {},
      });
    }
  }, [
    formMethods,
      wizardData.overrides,
    wizardData.dutyCycle.longHaul,
    wizardData.dutyCycle.regional,
    wizardData.dutyCycle.urban,
    wizardData.purchaseMethod,
    wizardData.scenario,
  ]);

  useEffect(() => {
    const subscription = formMethods.watch((values) => {
      const dutyCycle = values.dutyCycle as DutyCycle | undefined;
      updateWizard({
        scenario: values.scenario,
        purchaseMethod: values.purchaseMethod,
        dutyCycle: dutyCycle ?? wizardData.dutyCycle,
        overrides: values.overrides ?? {},
      });
    });
    return () => subscription.unsubscribe();
  }, [formMethods, updateWizard, wizardData.dutyCycle]);

  const goNext = async () => {
    if (!isLastStep) {
      const fieldsToValidate = stepFieldMap[stepIndex];
      if (fieldsToValidate?.length) {
        const isValid = await formMethods.trigger(fieldsToValidate);
        if (!isValid) {
          return;
        }
      }
      setStepIndex(Math.min(stepIndex + 1, steps.length - 1));
    }
  };

  const goPrev = () => setStepIndex(Math.max(stepIndex - 1, 0));

  const handleCalculate = async () => {
    if (!wizardData.currentVehicle) {
      return;
    }

    const vehicleIds = Array.from(
      new Set([wizardData.currentVehicle, ...wizardData.comparisonVehicles.filter(Boolean)])
    );

    const formValues = formMethods.getValues();
    const payload: ComparisonRequestPayload = {
      vehicle_ids: vehicleIds,
      scenario_name: formValues.scenario,
      purchase_method: formValues.purchaseMethod,
    };

    const overrides = compactOverrides(formValues.overrides ?? {});
    if (Object.keys(overrides).length) {
      payload.overrides = overrides;
    }

    try {
      const isValid = await formMethods.trigger();
      if (!isValid) {
        toast.error('Check the highlighted fields before running a comparison.');
        return;
      }
      await runComparison(payload);
      toast.success('Comparison ready. Redirecting to results.');
      navigate('/results');
    } catch (error) {
      console.error('Calculation failed', error);
      toast.error('Calculation failed. Please try again.');
    }
  };

  return (
    <FormProvider {...formMethods}>
      <div className="flex flex-col gap-6">
        <WizardStepper steps={steps} activeIndex={stepIndex} />

        {activeComponent}
        <SelectedVehiclesSummary />

        <Card className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-slate-900">
              Step {stepIndex + 1} of {steps.length}
            </p>
            {!baselineSelected && (
              <p className="text-xs text-rose-500">Select at least one vehicle to continue.</p>
            )}
          </div>
          <div className="flex gap-3">
            <Button variant="ghost" onClick={goPrev} disabled={stepIndex === 0 || isCalculating}>
              Back
            </Button>
            {isLastStep ? (
              <Button onClick={handleCalculate} disabled={!baselineSelected || isCalculating}>
                {isCalculating ? 'Calculating…' : 'Run comparison'}
              </Button>
            ) : (
              <Button onClick={() => void goNext()} disabled={!baselineSelected || isCalculating}>
                Next
              </Button>
            )}
          </div>
        </Card>
      </div>
    </FormProvider>
  );
};

export default WizardPage;
