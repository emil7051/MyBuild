import { SCENARIO_DEFINITIONS } from '@shared/data/scenarios';
import type { ScenarioKey } from '@shared/types/tco.types';

export const isScenarioKey = (value: string): value is ScenarioKey => {
  return Object.prototype.hasOwnProperty.call(SCENARIO_DEFINITIONS, value);
};

export const assertScenarioKey = (value: string): ScenarioKey => {
  if (isScenarioKey(value)) {
    return value;
  }

  throw new Error(`Unknown scenario key: ${value}`);
};

export const getScenarioKeys = (): ScenarioKey[] => {
  return Object.keys(SCENARIO_DEFINITIONS).map(assertScenarioKey);
};

export const getScenarioLabel = (scenarioIdentifier: string): string => {
  if (isScenarioKey(scenarioIdentifier)) {
    return SCENARIO_DEFINITIONS[scenarioIdentifier].name;
  }

  return scenarioIdentifier;
};
