import { useEffect } from 'react';
import { toast } from 'react-hot-toast';
import Button from '@components/shared/Button';
import ResultsPanel from '@components/results/ResultsPanel';
import { useTCOStore } from '@state/tcoStore';
import { useNavigate } from 'react-router-dom';

const ResultsPage = () => {
  const navigate = useNavigate();
  const lastRunCount = useTCOStore((state) => state.results.length);
  const isCalculating = useTCOStore((state) => state.isCalculating);
  const sessionId = useTCOStore((state) => state.sessionId);
  useEffect(() => {
    if (!isCalculating && lastRunCount === 0) {
      toast('Run the wizard to view results.');
      navigate('/', { replace: true });
    }
  }, [isCalculating, lastRunCount, navigate]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold text-slate-500">Results</p>
          <h2 className="text-2xl font-semibold text-slate-900">Cost comparison outputs</h2>
          <p className="text-sm text-slate-500">
            {isCalculating
              ? 'Running calculations…'
              : lastRunCount
                ? `Showing ${lastRunCount} vehicle${lastRunCount > 1 ? 's' : ''}.`
                : 'No data yet — run the wizard to populate this view.'}
          </p>
          {sessionId && (
            <p className="text-xs text-slate-500">
              Autosaved session:
              <span className="ml-1 font-mono text-slate-700">{sessionId}</span>
            </p>
          )}
        </div>
        <Button variant="secondary" onClick={() => navigate('/')}>Return to wizard</Button>
      </div>

      <ResultsPanel />
    </div>
  );
};

export default ResultsPage;
