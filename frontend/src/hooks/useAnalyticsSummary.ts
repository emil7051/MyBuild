import { useQuery } from '@tanstack/react-query';
import { fetchAnalyticsSummary } from '@services/api';

export const useAnalyticsSummary = () =>
  useQuery({
    queryKey: ['analytics-summary'],
    queryFn: fetchAnalyticsSummary,
    staleTime: 60_000,
  });
