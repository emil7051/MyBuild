import Card from '@components/shared/Card';
import { useTCOStore } from '@state/tcoStore';
import type { VehicleDetail } from '@shared/types/tco.types';
import { formatCurrency } from '@utils/format';

const metrics: {
  key: string;
  label: string;
  formatter: (detail: VehicleDetail) => string;
}[] = [
  {
    key: 'payload',
    label: 'Payload',
    formatter: (detail) => `${detail.payload.toFixed(1)} t`,
  },
  {
    key: 'range_km',
    label: 'Range (km)',
    formatter: (detail) =>
      detail.range_km > 0 ? `${detail.range_km.toLocaleString()} km` : 'Not specified',
  },
  {
    key: 'energy_store',
    label: 'Energy store',
    formatter: (detail) =>
      detail.drivetrain_type === 'BEV'
        ? `${detail.battery_capacity_kwh.toLocaleString()} kWh`
        : `${detail.litres_per_km.toFixed(2)} L/km`,
  },
  {
    key: 'annual_kms',
    label: 'Annual kms default',
    formatter: (detail) => `${detail.annual_kms.toLocaleString()} km`,
  },
  {
    key: 'annual_registration',
    label: 'Registration',
    formatter: (detail) => formatCurrency(detail.annual_registration),
  },
];

const SelectedVehiclesSummary = () => {
  const wizardData = useTCOStore((state) => state.wizardData);
  const vehicleDetails = useTCOStore((state) => state.vehicleDetails);
  const sessionId = useTCOStore((state) => state.sessionId);
  const selectedIds = Array.from(
    new Set(
      [wizardData.currentVehicle, ...wizardData.comparisonVehicles].filter(Boolean) as string[]
    )
  );
  const selectedDetails = selectedIds
    .map((id) => vehicleDetails[id])
    .filter(Boolean) as VehicleDetail[];

  if (!selectedIds.length) {
    return null;
  }

  return (
    <Card
      title="Selected vehicle specs"
      subtitle="Quick reference for your selected vehicle assumptions."
    >
      {sessionId && (
        <p className="mb-4 text-xs text-slate-500">
          Autosaved session:
          <span className="ml-1 font-mono text-slate-700">{sessionId}</span>
        </p>
      )}
      {!selectedDetails.length ? (
        <p className="text-sm text-slate-500">Fetching vehicle specifications…</p>
      ) : (
        <div className="overflow-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead>
              <tr>
                <th className="py-2 text-left font-semibold text-slate-500">Metric</th>
                {selectedDetails.map((detail) => (
                  <th
                    key={detail.vehicle_id}
                    className="py-2 text-right font-semibold text-slate-500"
                    title={`${detail.model_name} (${detail.vehicle_id})`}
                  >
                    <span className="block text-base text-slate-900">{detail.model_name}</span>
                    <span className="block text-xs font-normal text-slate-400">
                      {detail.weight_class}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {metrics.map((metric) => (
                <tr key={metric.key}>
                  <td className="py-2 text-slate-600">{metric.label}</td>
                  {selectedDetails.map((detail) => (
                    <td
                      key={`${detail.vehicle_id}-${metric.key}`}
                      className="py-2 text-right font-medium text-slate-900"
                    >
                      {metric.formatter(detail)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
};

export default SelectedVehiclesSummary;
