import { useEffect, useMemo, useState } from "react";
import PageShell from "../components/PageShell";
import Panel from "../components/Panel";
import AttackTable from "../components/soc/AttackTable";
import { getAttacksApi } from "../services/api";
import { connectAttackSocket } from "../services/socket";

function normalize(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.attacks)) return payload.attacks;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.results)) return payload.results;
  return [];
}

function keyOf(item) {
  return (
    item?.id ||
    `${item?.source_ip}-${item?.timestamp}-${item?.attack_type}`
  );
}

export default function AttackLogsPage({ profile, onLogout }) {
  const [attacks, setAttacks] = useState([]);
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("all");

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const response = await getAttacksApi(500);
        if (!active) return;

        const rows = normalize(response?.data ?? response);
        setAttacks(rows);
      } catch {
        if (active) setAttacks([]);
      }
    }

    load();
    const timer = setInterval(load, 5000);

    const disconnect = connectAttackSocket({
      onMessage(message) {
        const item = message?.data || message?.attack;
        if (!item) return;

        setAttacks((current) => {
          const merged = [item, ...current];
          const seen = new Set();

          return merged.filter((row) => {
            const key = keyOf(row);
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
          });
        });
      },
    });

    return () => {
      active = false;
      clearInterval(timer);
      disconnect?.();
    };
  }, []);

  const filtered = useMemo(() => {
    const query = search.toLowerCase();

    return attacks.filter((attack) => {
      const searchable = JSON.stringify(attack).toLowerCase();
      const matchesSearch = !query || searchable.includes(query);
      const matchesSeverity =
        severity === "all" ||
        String(attack?.severity).toLowerCase() === severity;

      return matchesSearch && matchesSeverity;
    });
  }, [attacks, search, severity]);

  return (
    <PageShell
      title="Attack Logs"
      profile={profile}
      onLogout={onLogout}
    >
      <div className="mx-auto max-w-[1600px] space-y-4">
        <div>
          <h2 className="text-2xl font-bold">Attack Logs</h2>
          <p className="text-sm text-slate-400">
            Complete log of all security events and responses
          </p>
        </div>

        <Panel>
          <div className="mb-4 flex flex-col gap-3 md:flex-row">
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search IP, attack type, location..."
              className="flex-1 rounded-lg border border-cyan-900 bg-[#041326] px-3 py-2 text-sm outline-none focus:border-cyan-400"
            />

            <select
              value={severity}
              onChange={(event) => setSeverity(event.target.value)}
              className="rounded-lg border border-cyan-900 bg-[#041326] px-3 py-2 text-sm"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <AttackTable attacks={filtered} />
        </Panel>
      </div>
    </PageShell>
  );
}