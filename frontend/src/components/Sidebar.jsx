import { NavLink } from "react-router-dom";
import {
  Activity,
  Bot,
  FileBarChart,
  FileText,
  HeartPulse,
  LayoutDashboard,
  Settings,
  Shield,
  ShieldAlert,
  X,
} from "lucide-react";

const navigationItems = [
  {
    label: "Dashboard",
    path: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Threats",
    path: "/threats",
    icon: ShieldAlert,
  },
  {
    label: "System Health",
    path: "/system-health",
    icon: HeartPulse,
  },
  {
    label: "Attack Logs",
    path: "/logs",
    icon: FileText,
  },
  {
    label: "Firewall",
    path: "/firewall",
    icon: Shield,
  },
  {
    label: "Reports",
    path: "/reports",
    icon: FileBarChart,
  },
  {
    label: "AI Assistant",
    path: "/assistant",
    icon: Bot,
  },
  {
    label: "Settings",
    path: "/settings",
    icon: Settings,
  },
];

function getInitials() {
  return "AI";
}

export default function Sidebar({
  open = false,
  onClose,
}) {
  return (
    <aside
      className={`fixed inset-y-0 left-0 z-50 flex w-[238px] flex-col border-r border-cyan-900/70 bg-[#03152b] shadow-2xl shadow-black/30 transition-transform duration-300 lg:translate-x-0 ${
        open ? "translate-x-0" : "-translate-x-full"
      }`}
    >
      <div className="flex h-16 shrink-0 items-center justify-between border-b border-cyan-900/70 px-4">
        <NavLink
          to="/dashboard"
          onClick={onClose}
          className="flex items-center gap-3"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-cyan-300/50 bg-cyan-500/20 text-cyan-300 shadow-[0_0_18px_rgba(34,211,238,0.18)]">
            <Shield size={20} />
          </div>

          <div>
            <p className="text-base font-bold tracking-wide text-white">
              AI SOC
            </p>

            <p className="text-[9px] text-cyan-300">
              Automated Firewall Response
            </p>
          </div>
        </NavLink>

        <button
          type="button"
          onClick={onClose}
          aria-label="Close navigation"
          className="rounded-md p-1 text-slate-400 hover:bg-slate-800 hover:text-white lg:hidden"
        >
          <X size={19} />
        </button>
      </div>

      <div className="border-b border-cyan-900/50 px-4 py-3">
        <div className="flex items-center gap-2 text-[10px] text-green-300">
          <span className="h-2 w-2 animate-pulse rounded-full bg-green-400" />
          SOC monitoring active
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        <p className="mb-3 px-3 text-[9px] font-semibold uppercase tracking-[0.2em] text-slate-600">
          Operations
        </p>

        {navigationItems.map(({ label, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            onClick={onClose}
            className={({ isActive }) =>
              `group flex items-center gap-3 rounded-lg border px-3 py-2.5 text-sm transition ${
                isActive
                  ? "border-cyan-500/40 bg-cyan-500/20 text-cyan-200 shadow-[0_0_14px_rgba(34,211,238,0.08)]"
                  : "border-transparent text-slate-300 hover:border-cyan-900 hover:bg-[#071a2f] hover:text-white"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  size={17}
                  className={
                    isActive
                      ? "text-cyan-300"
                      : "text-slate-400 group-hover:text-cyan-300"
                  }
                />

                <span className="flex-1">{label}</span>

                {label === "Threats" && (
                  <span className="rounded-full bg-red-500/20 px-1.5 py-0.5 text-[9px] text-red-300">
                    Live
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="shrink-0 border-t border-cyan-900/70 p-3">
        <div className="mb-3 flex items-center gap-3 rounded-lg border border-slate-800 bg-[#071a2f] p-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-cyan-600/30 text-xs font-bold text-cyan-200">
            {getInitials()}
          </div>

          <div className="min-w-0">
            <p className="truncate text-xs font-semibold text-white">
              SOC Analyst
            </p>
            <p className="truncate text-[10px] text-slate-500">
              Administrator
            </p>
          </div>

          <span className="ml-auto h-2 w-2 rounded-full bg-green-400" />
        </div>
      </div>
    </aside>
  );
}