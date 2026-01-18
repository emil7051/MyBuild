import { NavLink } from 'react-router-dom';
import type { PropsWithChildren } from 'react';

const AppShell = ({ children }: PropsWithChildren) => (
  <div className="min-h-screen bg-brand-background text-brand-text font-body">
    <header className="bg-white text-black border-b-4 border-brand-primary shadow-sm relative z-10">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 sm:px-6 py-5">
        <div>
          <p className="text-xs font-bold opacity-80">Energy Futures Foundation</p>
          <h1 className="text-2xl font-heading font-normal tracking-tight">
            Truck Cost Calculator
          </h1>
        </div>
        <nav className="flex gap-1 text-sm font-semibold tracking-wide">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `px-4 py-2 rounded-lg transition-all font-bold ${isActive
                ? 'bg-brand-primary text-black'
                : 'hover:bg-brand-primary/20'
              }`
            }
          >
            Compare
          </NavLink>
          <NavLink
            to="/results"
            className={({ isActive }) =>
              `px-4 py-2 rounded-lg transition-all font-bold ${isActive
                ? 'bg-brand-primary text-black'
                : 'hover:bg-brand-primary/20'
              }`
            }
          >
            Results
          </NavLink>
        </nav>
      </div>
    </header>
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-4 sm:px-6 py-8 md:py-12">
      {children}
    </main>
  </div>
);

export default AppShell;
