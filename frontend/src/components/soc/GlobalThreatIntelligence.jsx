import { useMemo } from "react";
import Panel from "../Panel";

function getRegionFromIp(ip = "") {
  const first = Number(String(ip).split(".")[0]);
  if (!Number.isFinite(first)) return "Unknown";
  if (first < 50) return "North America";
  if (first < 100) return "Europe";
  if (first < 150) return "Asia";
  if (first < 200) return "South America";
  return "Africa";
}

export default function GlobalThreatIntelligence({ attacks }) {
  const regionalData = useMemo(() => {
    const map = new Map();
    attacks.forEach((attack) => {
      const region = getRegionFromIp(attack?.source_ip);
      map.set(region, (map.get(region) || 0) + 1);
    });

    return [...map.entries()]
      .map(([region, count]) => ({ region, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  }, [attacks]);

  return (
    <Panel title="Global Threat Intelligence" className="bg-[#071a2f] border-cyan-900/60">
      {regionalData.length === 0 ? (
        <p className="text-xs text-slate-400">No global threat data yet.</p>
      ) : (
        <div className="space-y-2 text-xs">
          {regionalData.map((item) => (
            <div key={item.region} className="rounded-md border border-slate-800 bg-slate-900/40 px-3 py-2">
              <div className="mb-1 flex items-center justify-between">
                <span className="text-slate-300">{item.region}</span>
                <span className="text-cyan-200">{item.count}</span>
              </div>
              <div className="h-1.5 rounded bg-slate-800">
                <div className="h-1.5 rounded bg-cyan-400" style={{ width: `${Math.min(100, item.count * 8)}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </Panel>
  );
}
