import { NavLink } from "react-router-dom";
import Sidebar from "./Sidebar";

const MOBILE_NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/threats", label: "Threats" },
  { to: "/firewall", label: "Firewall" },
  { to: "/reports", label: "Reports" },
];

export default function PageShell({ title, profile, onLogout, children }) {
  return (
    <div className="min-h-screen bg-[#020b1c] text-slate-100">
      <Sidebar profile={profile} onLogout={onLogout} />

      <div className="lg:pl-56">
        <header className="sticky top-0 z-30 border-b border-cyan-900/50 bg-[#03152bcc] backdrop-blur">
          <div className="flex items-center justify-between gap-3 px-3 py-3 md:px-4">
            <div>
              <h1 className="text-base font-semibold text-white md:text-lg">{title || "Security Operations Center"}</h1>
              <p className="text-[11px] text-cyan-300">Real-time security monitoring</p>
            </div>

            <div className="flex items-center gap-3">
              <span className="hidden text-xs text-slate-300 sm:inline">{profile?.email || "soc@local"}</span>
              <button
                type="button"
                onClick={onLogout}
                className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-xs text-red-300 hover:bg-red-500/20 lg:hidden"
              >
                Logout
              </button>
            </div>
          </div>

          <nav className="flex gap-1 overflow-x-auto border-t border-cyan-900/30 px-2 py-2 lg:hidden">
            {MOBILE_NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `whitespace-nowrap rounded-md px-3 py-1.5 text-xs ${
                    isActive ? "bg-cyan-500/20 text-cyan-200" : "text-slate-300 hover:bg-slate-800"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </header>

        <main className="p-3 md:p-4">{children}</main>
      </div>
    </div>
  );
}
