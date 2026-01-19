import { useCallback, useEffect, useMemo, useRef } from 'react';
import { FormProvider, type FieldPath, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Card from '@components/shared/Card';
import Button from '@components/shared/Button';
import WizardDieselStep from '@components/wizard/WizardDieselStep';
import WizardElectricStep from '@components/wizard/WizardElectricStep';
import WizardCompareStep from '@components/wizard/WizardCompareStep';
import WizardStepper, { type WizardStep } from '@components/wizard/WizardStepper';
import { useCalculationRunner } from '@hooks/useCalculations';
import { useWizardAutosave } from '@hooks/useWizardAutosave';
import { useTCOStore } from '@state/tcoStore';
import { compactOverrides, compactVehicleParamOverrides } from '@utils/payload';
import type { ComparisonRequestPayload } from '@shared/types/tco.types';
import type { WizardFormValues } from '@forms/wizardForm';
import { wizardFormSchema } from '@forms/wizardForm';
import { toast } from 'react-hot-toast';

const steps: WizardStep[] = [
  {
    title: 'Your current truck',
    description: 'Select the diesel truck you operate today.',
  },
  {
    title: 'Electric options',
    description: 'Choose electric trucks to compare.',
  },
  {
    title: 'See your results',
    description: 'View results and explore scenarios.',
  },
];

const stepFieldMap: FieldPath<WizardFormValues>[][] = [
  [],
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
    'overrides.fuel_price_variation',
    'overrides.electricity_price_variation',
    'overrides.battery_life_variation',
    'overrides.charging_efficiency_variation',
  ],
];

const WizardPage = () => {
  const stepIndex = useTCOStore((state) => state.stepIndex);
  const setStepIndex = useTCOStore((state) => state.setStepIndex);
  const wizardData = useTCOStore((state) => state.wizardData);
  const isCalculating = useTCOStore((state) => state.isCalculating);
  const updateWizard = useTCOStore((state) => state.updateWizard);
  const { runComparison } = useCalculationRunner();
  useWizardAutosave();

  // Memoize form values to prevent unnecessary re-renders
  // This is the single source of truth flowing FROM the store TO the form
  const formValues = useMemo<WizardFormValues>(
    () => ({
      scenario: wizardData.scenario,
      purchaseMethod: wizardData.purchaseMethod,
      dutyCycle: wizardData.dutyCycle,
      overrides: wizardData.overrides ?? {},
    }),
    [wizardData.scenario, wizardData.purchaseMethod, wizardData.dutyCycle, wizardData.overrides]
  );

  const formMethods = useForm<WizardFormValues>({
    resolver: zodResolver(wizardFormSchema),
    mode: 'onTouched',
    // Use 'values' for reactive sync from store (not 'defaultValues')
    // This automatically updates form state when store changes
    values: formValues,
    // Keep dirty field values when external values change
    resetOptions: {
      keepDirtyValues: true,
    },
  });

  const isLastStep = stepIndex === steps.length - 1;
  const baselineSelected = Boolean(wizardData.currentVehicle);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const stepComponents = [
    <WizardDieselStep key="diesel" />,
    <WizardElectricStep key="electric" />,
    <WizardCompareStep key="compare" />,
  ];
  const activeComponent = stepComponents[stepIndex];

  // Debounced form-to-store sync
  // Only syncs user changes back to store, with debounce to avoid rapid updates
  const syncToStore = useCallback(
    (values: WizardFormValues) => {
      updateWizard({
        scenario: values.scenario,
        purchaseMethod: values.purchaseMethod,
        dutyCycle: values.dutyCycle,
        overrides: values.overrides ?? {},
      });
    },
    [updateWizard]
  );

  useEffect(() => {
    const subscription = formMethods.watch((values, { name, type }) => {
      console.log('[Form Watch]', { name, type, dutyCycle: values.dutyCycle });

      // Skip if any duty cycle value is undefined (fields not yet registered)
      if (
        values.dutyCycle?.urban === undefined ||
        values.dutyCycle?.regional === undefined ||
        values.dutyCycle?.longHaul === undefined
      ) {
        console.log('[Form Watch] Skipping - undefined duty cycle values');
        return;
      }

      // Debounce store updates to avoid rapid re-renders during typing
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
      debounceRef.current = setTimeout(() => {
        console.log('[Form Watch] Syncing to store:', values.dutyCycle);
        syncToStore(values as WizardFormValues);
      }, 150);
    });

    return () => {
      subscription.unsubscribe();
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [formMethods, syncToStore]);

  const validateCurrentStep = async () => {
    const fieldsToValidate = stepFieldMap[stepIndex];
    if (fieldsToValidate?.length) {
      return formMethods.trigger(fieldsToValidate);
    }
    return true;
  };

  const goNext = async () => {
    if (isLastStep || !baselineSelected) {
      return;
    }
    const isValid = await validateCurrentStep();
    if (!isValid) {
      return;
    }
    setStepIndex(Math.min(stepIndex + 1, steps.length - 1));
  };

  const goPrev = () => setStepIndex(Math.max(stepIndex - 1, 0));

  const handleStepClick = async (targetIndex: number) => {
    if (targetIndex === stepIndex) {
      return;
    }
    if (targetIndex > stepIndex && !baselineSelected) {
      return;
    }
    if (targetIndex > stepIndex) {
      const isValid = await validateCurrentStep();
      if (!isValid) {
        return;
      }
    }
    setStepIndex(Math.max(0, Math.min(targetIndex, steps.length - 1)));
  };

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
      duty_cycle: formValues.dutyCycle,
    };

    const overrides = compactOverrides(formValues.overrides ?? {});
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
      const isValid = await formMethods.trigger();
      if (!isValid) {
        toast.error('Check the highlighted fields before running a comparison.');
        return;
      }
      await runComparison(payload);
      toast.success('Comparison saved to your session.');
    } catch (error) {
      console.error('Calculation failed', error);
      toast.error('Calculation failed. Please try again.');
    }
  };

  return (
    <FormProvider {...formMethods}>
      <div className="flex flex-col gap-6">
        <WizardStepper steps={steps} activeIndex={stepIndex} onStepClick={handleStepClick} />

        {activeComponent}

        <Card className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-slate-900">
              Step {stepIndex + 1} of {steps.length}
            </p>
            {!baselineSelected && (
              <p className="text-xs text-rose-500">Select at least one truck to continue.</p>
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
