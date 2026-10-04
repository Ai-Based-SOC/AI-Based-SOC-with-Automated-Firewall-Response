import React from "react";
import { StatusBadge } from "./StatusBadge";

export function DataTable({ columns, data, loading = false, emptyMessage = "No data available", actions }) {
  if (loading) {
    return (
      <div className="h-64 bg-slate-900/50 rounded border border-slate-700/60 flex items-center justify-center text-slate-400">
        <div>Loading...</div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="h-64 bg-slate-900/50 rounded border border-slate-700/60 flex items-center justify-center text-slate-400">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full soc-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key} className="text-left text-sm font-medium text-slate-400 py-3">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr key={row.id || index} className="border-t border-slate-700/50">
              {columns.map((col) => {
                const value = row[col.key] || "-";
                const Badge = col.badge;
                if (Badge && row[col.key]) {
                  return (
                    <td key={`${col.key}-${index}`} className="py-3">
                      <StatusBadge status={value} variant={Badge.variant || "info"} size="sm" />
                    </td>
                  );
                }
                return (
                  <td key={`${col.key}-${index}`} className="py-3 text-slate-300 text-sm">
                    {value}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}