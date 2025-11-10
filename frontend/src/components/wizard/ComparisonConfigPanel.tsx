import WizardOperatingStep from '@components/wizard/WizardOperatingStep';
import WizardCostStep from '@components/wizard/WizardCostStep';

const ComparisonConfigPanel = () => (
  <div className="flex flex-col gap-6">
    <WizardOperatingStep />
    <WizardCostStep />
  </div>
);

export default ComparisonConfigPanel;
