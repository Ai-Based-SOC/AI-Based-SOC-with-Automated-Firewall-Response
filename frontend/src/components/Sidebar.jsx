import { NavLink } from "react-router-dom";
import { BarChart3, ShieldAlert, ShieldCheck, FileText, LogOut } from "lucide-react";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { to: "/threats", label: "Threat Analysis", icon: ShieldAlert },
  { to: "/firewall", label: "Firewall", icon: ShieldCheck },
  { to: "/reports", label: "Reports", icon: FileText },
];

export default function Sidebar({ profile, onLogout }) {
  const initials = (profile?.email || "SOC").slice(0, 2).toUpperCase();

  return (
    <aside className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:z-40 lg:flex lg:w-56 lg:flex-col lg:border-r lg:border-cyan-900/60 lg:bg-[#031428]">
      <div className="border-b border-cyan-900/60 px-4 py-4">
        <p className="text-sm font-semibold tracking-wide text-cyan-200">AI-SOC Command</p>
        <p className="text-[11px] text-cyan-400/80">Automated Firewall Response</p>
      </div>

      <nav className="flex-1 space-y-1.5 px-3 py-4">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition ${
                  isActive
                    ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/30"
                    : "text-slate-300 hover:bg-slate-800/70 hover:text-white"
                }`
              }
            >
              <Icon size={16} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="border-t border-cyan-900/60 px-3 py-3">
        <div className="mb-3 flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-900/50 p-2">
          <div className="grid h-8 w-8 place-items-center rounded-full bg-cyan-500/30 text-xs font-semibold text-cyan-100">
            {initials}
          </div>
          <div className="min-w-0">
            <p className="truncate text-xs text-white">{profile?.email || "soc@local"}</p>
            <p className="text-[10px] text-slate-400">SOC Analyst</p>
          </div>
        </div>

        <button
          type="button"
          onClick={onLogout}
          className="flex w-full items-center justify-center gap-2 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300 hover:bg-red-500/20"
        >
          <LogOut size={14} />
          Logout
        </button>
      </div>
    </aside>
  );
}
