import { SCENARIO_DEFINITIONS } from '@shared/data/scenarios';
import { ScenarioKey } from '@shared/types/tco.types';

const isScenarioKey = (value: string): value is ScenarioKey => {
  return Object.prototype.hasOwnProperty.call(SCENARIO_DEFINITIONS, value);
};

export const getScenarioLabel = (scenarioIdentifier: string): string => {
  if (isScenarioKey(scenarioIdentifier)) {
    return SCENARIO_DEFINITIONS[scenarioIdentifier].name;
  }

  return scenarioIdentifier;
};
