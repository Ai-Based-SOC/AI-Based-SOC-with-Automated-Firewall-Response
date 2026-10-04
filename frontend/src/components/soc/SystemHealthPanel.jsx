import { useMemo } from "react";
import Panel from "../Panel";

function formatTime(value) {
  const date = value ? new Date(value) : null;
  if (!date || Number.isNaN(date.getTime())) return "No data";
  return date.toLocaleTimeString();
}

export default function SystemHealthPanel({ attacks, wsConnected, apiHealthy }) {
  const { lastEvent, highRiskCount, blockedCount } = useMemo(() => {
    const latest = attacks[0];
    const highRisk = attacks.filter((item) => Number(item?.risk_score || 0) >= 80).length;
    const blocked = attacks.filter((item) => /block/i.test(String(item?.action_taken || ""))).length;
    return {
      lastEvent: latest?.timestamp || latest?.created_at || latest?.detected_at || latest?.event_time,
      highRiskCount: highRisk,
      blockedCount: blocked,
    };
  }, [attacks]);

  const rows = [
    { label: "API Health", value: apiHealthy ? "Online" : "Checking", color: apiHealthy ? "text-green-300" : "text-amber-300" },
    { label: "Socket", value: wsConnected ? "Connected" : "Reconnecting", color: wsConnected ? "text-green-300" : "text-amber-300" },
    { label: "Last Event", value: formatTime(lastEvent), color: "text-cyan-200" },
    { label: "High Risk", value: String(highRiskCount), color: "text-orange-300" },
    { label: "Blocked", value: String(blockedCount), color: "text-cyan-300" },
  ];

  return (
    <Panel title="System Health" className="bg-[#071a2f] border-cyan-900/60">
      <div className="space-y-2">
        {rows.map((row) => (
          <div key={row.label} className="flex items-center justify-between rounded-md border border-slate-800 bg-slate-900/40 px-3 py-2 text-xs">
            <span className="text-slate-400">{row.label}</span>
            <span className={row.color}>{row.value}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}
