import { Suspense, lazy } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import AppShell from '@components/layout/AppShell';
import WizardPage from '@pages/WizardPage';

const ResultsPage = lazy(() => import('@pages/ResultsPage'));

const RouteLoadingFallback = () => (
  <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-500">
    Loading page...
  </div>
);

const App = () => (
  <AppShell>
    <Routes>
      <Route path="/" element={<WizardPage />} />
      <Route
        path="/results"
        element={(
          <Suspense fallback={<RouteLoadingFallback />}>
            <ResultsPage />
          </Suspense>
        )}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </AppShell>
);

export default App;
