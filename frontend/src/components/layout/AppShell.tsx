import { NavLink } from 'react-router-dom';
import type { PropsWithChildren } from 'react';

const AppShell = ({ children }: PropsWithChildren) => (
  <div className="min-h-screen bg-slate-50 text-slate-900">
    <header className="bg-white shadow-sm border-b border-slate-200">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Energy Futures Foundation</p>
          <h1 className="text-xl font-semibold text-slate-900">
            Total Cost of Ownership Comparison Tool
          </h1>
        </div>
        <nav className="flex gap-4 text-sm">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `rounded px-3 py-2 font-medium ${
                isActive ? 'bg-brand-100 text-brand-700' : 'text-slate-500 hover:text-slate-900'
              }`
            }
          >
            Wizard
          </NavLink>
          <NavLink
            to="/results"
            className={({ isActive }) =>
              `rounded px-3 py-2 font-medium ${
                isActive ? 'bg-brand-100 text-brand-700' : 'text-slate-500 hover:text-slate-900'
              }`
            }
          >
            Results
          </NavLink>
        </nav>
      </div>
    </header>
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-6 py-8">
      {children}
    </main>
  </div>
);

export default AppShell;
