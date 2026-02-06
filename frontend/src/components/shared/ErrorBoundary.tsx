import { Component, type ErrorInfo, type ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  retryCount: number;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {
    hasError: false,
    error: undefined,
    retryCount: 0,
  };

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('Unhandled application error', error, errorInfo);
  }

  handleRetry = () => {
    this.setState((prev) => ({
      hasError: false,
      error: undefined,
      retryCount: prev.retryCount + 1,
    }));
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
          <div className="w-full max-w-lg rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Something went wrong
            </p>
            <h1 className="mt-2 text-2xl font-heading font-bold text-black">
              We hit an unexpected error.
            </h1>
            <p className="mt-2 text-sm text-slate-600">
              Try again to recover. If this keeps happening, refresh the page and rerun your
              comparison.
            </p>
            {import.meta.env.DEV && this.state.error && (
              <p className="mt-3 rounded bg-slate-100 px-3 py-2 font-mono text-xs text-slate-700">
                {this.state.error.message}
              </p>
            )}
            <div className="mt-5 flex gap-3">
              <button
                type="button"
                onClick={this.handleRetry}
                className="rounded-md bg-brand-primary px-4 py-2 text-sm font-semibold text-black transition hover:brightness-95"
              >
                Try again
              </button>
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
              >
                Reload page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return <div key={this.state.retryCount}>{this.props.children}</div>;
  }
}

export default ErrorBoundary;
