import {
  Bell,
  ChevronDown,
  Menu,
  UserCircle,
} from "lucide-react";

function getDisplayName(profile) {
  return (
    profile?.full_name ||
    profile?.name ||
    profile?.username ||
    profile?.email ||
    "admin"
  );
}

function getRole(profile) {
  return profile?.role || "Administrator";
}

export default function TopBar({
  title,
  profile,
  onLogout,
  onMenuClick,
}) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-cyan-900/70 bg-[#041326]/95 px-4 shadow-lg shadow-black/10 backdrop-blur-md md:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          aria-label="Open navigation"
          className="rounded-lg border border-cyan-900 p-2 text-slate-300 hover:bg-cyan-950 hover:text-white lg:hidden"
        >
          <Menu size={20} />
        </button>

        <div className="min-w-0">
          <h1 className="truncate text-base font-bold text-white md:text-lg">
            {title || "AI SOC"}
          </h1>

          <p className="truncate text-[10px] text-cyan-300">
            Real-time security monitoring and automated response
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-2 rounded-full border border-green-500/30 bg-green-500/10 px-3 py-1.5 text-[10px] text-green-300 md:flex">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-green-400" />
          System Operational
        </div>

        <button
          type="button"
          aria-label="Notifications"
          className="relative rounded-lg p-2 text-slate-300 hover:bg-slate-800 hover:text-white"
        >
          <Bell size={18} />

          <span className="absolute right-0.5 top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[9px] font-bold text-white">
            3
          </span>
        </button>

        <div className="hidden items-center gap-2 sm:flex">
          <UserCircle size={25} className="text-cyan-300" />

          <div className="max-w-[140px]">
            <p className="truncate text-xs font-semibold text-white">
              {getDisplayName(profile)}
            </p>

            <p className="truncate text-[10px] text-slate-500">
              {getRole(profile)}
            </p>
          </div>

          <ChevronDown size={14} className="text-slate-500" />
        </div>

        <button
          type="button"
          onClick={onLogout}
          className="hidden rounded-lg border border-red-500/30 px-3 py-1.5 text-[10px] text-red-300 transition hover:bg-red-500/10 sm:block"
        >
          Logout
        </button>
      </div>
    </header>
  );
}