import type { ReactNode } from 'react';

interface EmptyChartStateProps {
  message: ReactNode;
}

const EmptyChartState = ({ message }: EmptyChartStateProps) => (
  <div className="flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-slate-200">
    <p className="text-sm text-slate-500">{message}</p>
  </div>
);

export default EmptyChartState;
