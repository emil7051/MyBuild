import { describe, it, expect, beforeEach } from 'vitest';
import { useTCOStore } from '@state/tcoStore';
import type { TCOResult } from '@shared/types/tco.types';

describe('TCO Store State Management', () => {
  beforeEach(() => {
    // Reset store between tests
    useTCOStore.setState({
      stepIndex: 0,
      wizardData: {
        currentVehicle: undefined,
        comparisonVehicles: [],
        scenario: 'baseline',
        purchaseMethod: 'financed',
        dutyCycle: { urban: 60, regional: 25, longHaul: 15 },
        overrides: {},
        vehicleParamOverrides: {},
      },
      results: [],
      isCalculating: false,
      sessionId: undefined,
    });
  });

  describe('Duty Cycle Validation', () => {
    it('should replace NaN duty cycle values with defaults', () => {
      const store = useTCOStore.getState();

      store.updateWizard({
        dutyCycle: { urban: NaN, regional: 25, longHaul: 15 },
      });

      const updated = useTCOStore.getState();
      // Should fallback to defaults when any value is NaN
      expect(updated.wizardData.dutyCycle.urban).toBe(60);
      expect(updated.wizardData.dutyCycle.regional).toBe(25);
      expect(updated.wizardData.dutyCycle.longHaul).toBe(15);
    });

    it('should clamp negative duty cycle values to zero', () => {
      const store = useTCOStore.getState();

      store.updateWizard({
        dutyCycle: { urban: -10, regional: 25, longHaul: 15 },
      });

      const updated = useTCOStore.getState();
      expect(updated.wizardData.dutyCycle.urban).toBe(0);
      expect(updated.wizardData.dutyCycle.regional).toBe(25);
      expect(updated.wizardData.dutyCycle.longHaul).toBe(15);
    });

    it('should accept valid duty cycle values', () => {
      const store = useTCOStore.getState();

      store.updateWizard({
        dutyCycle: { urban: 50, regional: 30, longHaul: 20 },
      });

      const updated = useTCOStore.getState();
      expect(updated.wizardData.dutyCycle.urban).toBe(50);
      expect(updated.wizardData.dutyCycle.regional).toBe(30);
      expect(updated.wizardData.dutyCycle.longHaul).toBe(20);
    });

    it('should handle all-NaN duty cycle values', () => {
      const store = useTCOStore.getState();

      store.updateWizard({
        dutyCycle: { urban: NaN, regional: NaN, longHaul: NaN },
      });

      const updated = useTCOStore.getState();
      // Should fallback to all defaults
      expect(updated.wizardData.dutyCycle).toEqual({
        urban: 60,
        regional: 25,
        longHaul: 15,
      });
    });

    it('should clamp all negative values', () => {
      const store = useTCOStore.getState();

      store.updateWizard({
        dutyCycle: { urban: -5, regional: -10, longHaul: -15 },
      });

      const updated = useTCOStore.getState();
      expect(updated.wizardData.dutyCycle).toEqual({
        urban: 0,
        regional: 0,
        longHaul: 0,
      });
    });
  });

  describe('Other WizardData Updates', () => {
    it('should update scenario without affecting duty cycle', () => {
      const store = useTCOStore.getState();

      store.updateWizard({
        scenario: 'technology_breakthrough',
      });

      const updated = useTCOStore.getState();
      expect(updated.wizardData.scenario).toBe('technology_breakthrough');
      expect(updated.wizardData.dutyCycle).toEqual({
        urban: 60,
        regional: 25,
        longHaul: 15,
      });
    });

    it('should update current vehicle', () => {
      const store = useTCOStore.getState();

      store.updateWizard({
        currentVehicle: 'BEV001',
      });

      const updated = useTCOStore.getState();
      expect(updated.wizardData.currentVehicle).toBe('BEV001');
    });

    it('should update comparison vehicles', () => {
      const store = useTCOStore.getState();

      store.updateWizard({
        comparisonVehicles: ['DSL001', 'BEV002'],
      });

      const updated = useTCOStore.getState();
      expect(updated.wizardData.comparisonVehicles).toEqual([
        'DSL001',
        'BEV002',
      ]);
    });
  });

  describe('Results Management', () => {
    it('should set results and maintain order based on wizard data', () => {
      const store = useTCOStore.getState();

      // First set the wizard data with vehicle order
      store.updateWizard({
        currentVehicle: 'BEV001',
        comparisonVehicles: ['DSL001'],
      });

      // Then set results in different order
      store.setResults([
        { vehicle_id: 'DSL001', total_cost: 100000, breakdown: {} } as unknown as TCOResult,
        { vehicle_id: 'BEV001', total_cost: 150000, breakdown: {} } as unknown as TCOResult,
      ]);

      const updated = useTCOStore.getState();
      // Results should be reordered to match wizard data order
      expect(updated.results[0].vehicle_id).toBe('BEV001');
      expect(updated.results[1].vehicle_id).toBe('DSL001');
    });

    it('should reset results', () => {
      const store = useTCOStore.getState();

      store.setResults([
        { vehicle_id: 'BEV001', total_cost: 150000, breakdown: {} } as unknown as TCOResult,
      ]);

      expect(useTCOStore.getState().results).toHaveLength(1);

      store.resetResults();

      expect(useTCOStore.getState().results).toHaveLength(0);
    });
  });

  describe('Session Management', () => {
    it('should set session ID', () => {
      const store = useTCOStore.getState();

      store.setSessionId('test-session-123');

      expect(useTCOStore.getState().sessionId).toBe('test-session-123');
    });

    it('should clear session ID', () => {
      const store = useTCOStore.getState();

      store.setSessionId('test-session-123');
      store.setSessionId(undefined);

      expect(useTCOStore.getState().sessionId).toBeUndefined();
    });
  });

  describe('Calculating State', () => {
    it('should track calculating state', () => {
      const store = useTCOStore.getState();

      expect(store.isCalculating).toBe(false);

      store.setIsCalculating(true);
      expect(useTCOStore.getState().isCalculating).toBe(true);

      store.setIsCalculating(false);
      expect(useTCOStore.getState().isCalculating).toBe(false);
    });
  });
});
