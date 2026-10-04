import React from "react";
import { ShieldAlert, AlertTriangle, Activity, BrainCircuit, Target, MapPin, TrendingUp, Logs, ShieldCheck } from "lucide-react";

export function KPIStatCard({ title, value, kind = "default", icon = ShieldAlert, change = 0, comparison = "vs last period", showBorder = true }) {
  const kindStyles = {
    critical: { bg: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", color: "#EF4444" },
    warning: { bg: "rgba(245, 158, 11, 0.1)", border: "1px solid rgba(245, 158, 11, 0.3)", color: "#F59E0B" },
    info: { bg: "rgba(56, 189, 248, 0.1)", border: "1px solid rgba(56, 189, 248, 0.3)", color: "#38BDF8" },
    good: { bg: "rgba(34, 197, 94, 0.1)", border: "1px solid rgba(34, 197, 94, 0.3)", color: "#22C55E" },
    success: { bg: "rgba(16, 185, 129, 0.1)", border: "1px solid rgba(16, 185, 129, 0.3)", color: "#10B981" },
    default: { bg: "rgba(107, 114, 128, 0.1)", border: "1px solid rgba(107, 114, 128, 0.3)", color: "#71717A" }
  };

  const styleKind = kindStyles[kind] || kindStyles.default;
  const changeClass = change > 0 ? "text-green-400" : change < 0 ? "text-red-400" : "text-slate-400";
  const changeArrows = change > 0 ? "▲" : change < 0 ? "▼" : "—";

  return (
    <article
      className={`metric-card rounded-lg border ${showBorder ? "border-slate-700/50" : ""} transition-colors hover:border-cyan-500/30 cursor-pointer`}
      style={styleKind}
    >
      <div className="metric-top flex flex-col md:flex-row items-start md:items-center justify-between pt-3">
        <span className="text-xs font-medium uppercase tracking-wider opacity-80 {styleKind.color}">{title}</span>
        <span className="text-xs font-medium opacity-80 {changeClass}">{changeArrows} {Math.abs(change)}%</span>
      </div>
      <div className="metric-value text-3xl font-bold mt-1 {styleKind.color}">
        {value}
      </div>
      <p className="text-xs mt-1 opacity-60">
        {comparison}
      </p>
    </article>
  );
}

export function KPIGrid({ kpis }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {kpis.map((kpi) => (
        <KPIStatCard
          key={kpi.id}
          title={kpi.title}
          value={kpi.value}
          kind={kpi.kind || "default"}
          icon={kpi.icon}
          change={kpi.change || 0}
          comparison={kpi.comparison || "vs last period"}
        />
      ))}
    </div>
  );
}