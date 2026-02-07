import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import EmptyChartState from '@components/results/EmptyChartState';

const renderState = (message: string): string =>
  renderToStaticMarkup(<EmptyChartState message={message} />);

describe('EmptyChartState', () => {
  it('renders the default no-results state', () => {
    expect(renderState('No results to display')).toMatchInlineSnapshot(
      `"<div class=\\"flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-slate-200\\"><p class=\\"text-sm text-slate-500\\">No results to display</p></div>"`
    );
  });

  it('renders comparison guidance messaging', () => {
    expect(
      renderState('Compare both diesel and electric vehicles to see savings breakdown')
    ).toMatchInlineSnapshot(
      `"<div class=\\"flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-slate-200\\"><p class=\\"text-sm text-slate-500\\">Compare both diesel and electric vehicles to see savings breakdown</p></div>"`
    );
  });

  it('renders calculation fallback messaging', () => {
    expect(renderState('Unable to build payback timeline.')).toMatchInlineSnapshot(
      `"<div class=\\"flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-slate-200\\"><p class=\\"text-sm text-slate-500\\">Unable to build payback timeline.</p></div>"`
    );
  });
});
