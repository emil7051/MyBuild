import { useMemo } from 'react';
import { VEHICLE_SUMMARIES } from '@shared/data/vehicleCatalog';

export const useVehicleCatalog = () => {
  const data = useMemo(() => VEHICLE_SUMMARIES, []);
  return {
    data,
    isLoading: false,
  };
};
