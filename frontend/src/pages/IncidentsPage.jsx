import React, { useEffect, useState } from "react";
import { Panel } from "../components/Panel";
import { StatusBadge } from "../components/StatusBadge";
import * as API from "../services/api";

export default function IncidentsPage({ profile }) {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [open, setOpen] = useState(0);
  const [critical, setCritical] = useState(0);
  const [high, setHigh] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadIncidents() {
      setLoading(true);
      setError("");

      try {
        const response = await API.getIncidentsApi(page, pageSize);

        if (cancelled) return;

        const data = Array.isArray(response?.data)
          ? response.data
          : [];

        const headers = response?.headers || {};

        setIncidents(data);

        const totalHeader =
          headers["x-total-count"] ??
          headers["X-Total-Count"];

        setTotal(
          totalHeader !== undefined
            ? parseInt(totalHeader, 10) || 0
            : data.length
        );

        setOpen(
          data.filter(
            (incident) =>
              String(incident?.status || "").toLowerCase() === "open"
          ).length
        );

        setCritical(
          data.filter(
            (incident) =>
              String(incident?.severity || "").toLowerCase() ===
              "critical"
          ).length
        );

        setHigh(
          data.filter(
            (incident) =>
              String(incident?.severity || "").toLowerCase() === "high"
          ).length
        );
      } catch (e) {
        if (cancelled) return;

        setError(
          e?.response?.data?.detail ||
            e?.message ||
            "Failed to load incidents"
        );

        setIncidents([]);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadIncidents();

    return () => {
      cancelled = true;
    };
  }, [page, pageSize]);

  const totalPages = Math.max(
    1,
    Math.ceil(total / pageSize)
  );

  return (
    <div className="min-h-screen bg-[#020b1c] text-white p-6">
      <h1 className="soc-heading mb-6">Incidents</h1>

      {/* Incident List */}
      <Panel title="Incident List">
        <div className="h-96 overflow-auto">
          {loading ? (
            <div className="flex items-center justify-center h-full text-slate-400">
              Loading incidents…
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-red-400">
                {error}
              </div>
            </div>
          ) : incidents.length > 0 ? (
            incidents.map((incident) => (
              <div
                key={incident.id}
                className="flex items-center justify-between border-b border-slate-700/50 py-3"
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono text-cyan-400 w-8">
                    {incident.id}
                  </span>

                  <div>
                    <div className="text-white">
                      {incident.title ||
                        incident.name ||
                        "Untitled Incident"}
                    </div>

                    {incident.source_ip && (
                      <div className="text-xs text-slate-500 font-mono">
                        {incident.source_ip}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <StatusBadge
                    status={incident.severity || "unknown"}
                    variant="critical"
                    size="sm"
                  />

                  <span className="text-slate-400 text-sm">
                    {incident.status || "Unknown"}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className="flex items-center justify-center h-full text-slate-400">
              No incidents found.
            </div>
          )}
        </div>
      </Panel>

      {/* Incident Stats */}
      <div className="mt-6">
        <Panel title="Incident Stats">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-slate-400">
                Total Incidents
              </div>

              <div className="text-xl font-medium text-cyan-400">
                {total}
              </div>
            </div>

            <div>
              <div className="text-sm text-slate-400">
                Open
              </div>

              <div className="text-xl font-medium text-red-400">
                {open}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mt-4">
            <div>
              <div className="text-sm text-slate-400">
                Critical
              </div>

              <div className="text-xl font-medium text-red-600">
                {critical}
              </div>
            </div>

            <div>
              <div className="text-sm text-slate-400">
                High
              </div>

              <div className="text-xl font-medium text-orange-400">
                {high}
              </div>
            </div>
          </div>
        </Panel>
      </div>

      {/* Pagination */}
      <div className="mt-6 flex items-center justify-between">
        <div className="text-sm text-slate-400">
          Page {page} of {totalPages}
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            className="soc-btn soc-btn-secondary"
            disabled={page <= 1 || loading}
            onClick={() =>
              setPage((current) => Math.max(1, current - 1))
            }
          >
            Previous
          </button>

          <button
            type="button"
            className="soc-btn"
            disabled={page >= totalPages || loading}
            onClick={() =>
              setPage((current) =>
                Math.min(totalPages, current + 1)
              )
            }
          >
            Next
          </button>

          <select
            value={pageSize}
            onChange={(event) => {
              setPageSize(Number(event.target.value));
              setPage(1);
            }}
            className="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm text-white"
          >
            <option value={10}>10 / page</option>
            <option value={20}>20 / page</option>
            <option value={50}>50 / page</option>
            <option value={100}>100 / page</option>
          </select>
        </div>
      </div>

      {/* Actions */}
      <div className="mt-8 pt-8 border-t border-slate-700/40">
        <h2 className="soc-heading mb-4">
          Actions
        </h2>

        <div className="space-y-2">
          <button
            type="button"
            className="soc-btn"
          >
            Create New Incident
          </button>

          <button
            type="button"
            className="soc-btn soc-btn-secondary"
          >
            Import Incidents
          </button>
        </div>
      </div>
    </div>
  );
}