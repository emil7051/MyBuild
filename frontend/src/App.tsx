import { Navigate, Route, Routes } from 'react-router-dom';
import AppShell from '@components/layout/AppShell';
import ResultsPage from '@pages/ResultsPage';
import WizardPage from '@pages/WizardPage';

const App = () => (
  <AppShell>
    <Routes>
      <Route path="/" element={<WizardPage />} />
      <Route path="/results" element={<ResultsPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </AppShell>
);

export default App;
