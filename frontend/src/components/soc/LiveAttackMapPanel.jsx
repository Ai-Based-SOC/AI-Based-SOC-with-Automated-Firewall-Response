import { useMemo } from "react";
import Panel from "../Panel";

function hashToPosition(ip = "") {
  let hash = 0;
  for (let i = 0; i < ip.length; i += 1) {
    hash = (hash * 31 + ip.charCodeAt(i)) >>> 0;
  }
  const x = 8 + (hash % 84);
  const y = 12 + ((hash >> 8) % 68);
  return { x, y };
}

function getSeverityColor(severity = "") {
  const value = String(severity).toLowerCase();
  if (value === "critical") return "#ef4444";
  if (value === "high") return "#f97316";
  if (value === "medium") return "#eab308";
  return "#22d3ee";
}

export default function LiveAttackMapPanel({ attacks }) {
  const markers = useMemo(
    () =>
      attacks.slice(0, 36).map((attack, index) => {
        const source = attack?.source_ip || attack?.ip || `unknown-${index}`;
        const destination = attack?.destination_ip || "core";
        return {
          id: attack?.id || `${source}-${attack?.timestamp || index}`,
          source,
          destination,
          severity: attack?.severity || "low",
          ...hashToPosition(source),
        };
      }),
    [attacks]
  );

  return (
    <Panel title="Live Attack Map" className="bg-[#071a2f] border-cyan-900/60">
      <div className="h-56 overflow-hidden rounded-lg border border-cyan-900/60 bg-[#041224]">
        <svg viewBox="0 0 100 50" className="h-full w-full">
          <rect x="0" y="0" width="100" height="50" fill="#021225" />
          <ellipse cx="16" cy="25" rx="11" ry="8" fill="#0a2746" />
          <ellipse cx="38" cy="21" rx="14" ry="9" fill="#0a2746" />
          <ellipse cx="56" cy="29" rx="12" ry="8" fill="#0a2746" />
          <ellipse cx="74" cy="19" rx="13" ry="8" fill="#0a2746" />
          <ellipse cx="89" cy="30" rx="8" ry="6" fill="#0a2746" />

          {markers.map((marker) => (
            <g key={marker.id}>
              <line x1={marker.x} y1={marker.y} x2="50" y2="25" stroke={getSeverityColor(marker.severity)} strokeOpacity="0.5" strokeWidth="0.3" />
              <circle cx={marker.x} cy={marker.y} r="1.1" fill={getSeverityColor(marker.severity)}>
                <animate attributeName="r" values="1.1;2.5;1.1" dur="2s" repeatCount="indefinite" />
              </circle>
            </g>
          ))}

          <circle cx="50" cy="25" r="2" fill="#22d3ee" />
          <text x="52" y="24" fill="#67e8f9" fontSize="2.2">SOC</text>
        </svg>
      </div>

      <p className="mt-3 text-xs text-slate-300">Showing {markers.length} latest attack origins routed to monitored infrastructure.</p>
    </Panel>
  );
}
