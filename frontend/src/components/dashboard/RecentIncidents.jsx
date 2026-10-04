import React from "react";
import { StatusBadge } from "../StatusBadge";

const incidentStatuses = [
  { label: "Open", color: "red-500" },
  { label: "Investigating", color: "orange-500" },
  { label: "In Progress", color: "amber-600" },
  { label: "Resolved", color: "green-500" },
  { label: "Closed", color: "slate-500" }
];

export function RecentIncidents({ incidents }) {
  return (
    <div>
      <h3 className="soc-heading mb-3">Recent Incidents</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-slate-400">
          <thead>
            <tr className="border-b border-slate-700/50 border-solid">
              <th className="text-left font-medium text-white py-3">Incident ID</th>
              <th className="text-left font-medium text-white py-3">Title</th>
              <th className="text-left font-medium text-white py-3">Severity</th>
              <th className="text-left font-medium text-white py-3">Status</th>
              <th className="text-left font-medium text-white py-3">Time</th>
            </tr>
          </thead>
          <tbody>
            {incidents && incidents.map((incident) => (
              <tr key={incident.id} className="border-b border-slate-700/50 border-solid py-3">
                <td className="font-mono text-cyan-400 font-medium">
                  {incident.id}
                </td>
                <td>
                  <span className="font-medium text-white">{incident.title}</span>
                </td>
                <td>
                  <StatusBadge status={incident.severity} variant="critical" size="sm" />
                </td>
                <td>
                  <span className={`text-slate-400 text-xs font-medium ${
                    incident.severity === "critical"
                      ? "red-400"
                      : incident.severity === "high"
                        ? "orange-400"
                        : incident.severity === "medium"
                          ? "amber-600"
                          : "green-500"
                  }`}
                >
                  {incident.status}
                </span>
                </td>
                <td className="text-slate-500 text-xs">
                  {incident.created_at || "N/A"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 text-right">
        <button className="soc-btn soc-btn-sm text-slate-400 hover:text-cyan-400 transition-colors">
          View All
        </button>
      </div>
    </div>
  );
}