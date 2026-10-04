import Panel from "../Panel";

function formatTimestamp(value) {
  const date = value ? new Date(value) : null;
  if (!date || Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString();
}

function badgeClass(severity = "") {
  const value = String(severity).toLowerCase();
  if (value === "critical") return "bg-red-500/20 text-red-300 border-red-500/30";
  if (value === "high") return "bg-orange-500/20 text-orange-300 border-orange-500/30";
  if (value === "medium") return "bg-yellow-500/20 text-yellow-300 border-yellow-500/30";
  return "bg-cyan-500/20 text-cyan-300 border-cyan-500/30";
}

export default function RecentSecurityActivity({ attacks }) {
  return (
    <Panel title="Recent Security Activity" className="bg-[#071a2f] border-cyan-900/60">
      <div className="max-h-72 overflow-auto rounded-lg border border-slate-800">
        <table className="w-full text-left text-xs">
          <thead className="sticky top-0 bg-[#071120] text-slate-300">
            <tr>
              <th className="px-3 py-2">Time</th>
              <th className="px-3 py-2">Source</th>
              <th className="px-3 py-2">Destination</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Severity</th>
              <th className="px-3 py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {attacks.length === 0 ? (
              <tr>
                <td className="px-3 py-4 text-slate-400" colSpan={6}>
                  No attack activity available.
                </td>
              </tr>
            ) : (
              attacks.map((item, index) => (
                <tr key={item?.id || `${item?.source_ip}-${item?.timestamp || index}`} className="border-t border-slate-800/80">
                  <td className="px-3 py-2 text-slate-300">{formatTimestamp(item?.timestamp || item?.created_at || item?.detected_at || item?.event_time)}</td>
                  <td className="px-3 py-2 text-cyan-200">{item?.source_ip || "-"}</td>
                  <td className="px-3 py-2 text-slate-300">{item?.destination_ip || "-"}</td>
                  <td className="px-3 py-2 text-slate-200">{item?.attack_type || "Unknown"}</td>
                  <td className="px-3 py-2">
                    <span className={`rounded-full border px-2 py-0.5 ${badgeClass(item?.severity)}`}>{item?.severity || "low"}</span>
                  </td>
                  <td className="px-3 py-2 text-slate-300">{item?.action_taken || item?.status || "monitor"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
