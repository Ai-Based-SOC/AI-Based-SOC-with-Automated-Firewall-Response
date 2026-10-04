import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Activity, AlertTriangle, Bot, Radar, Shield, ShieldAlert, ShieldCheck, Target } from "lucide-react";
import PageShell from "../components/PageShell";
import { getAttacksApi, healthApi } from "../services/api";
import { connectAttackSocket } from "../services/socket";
import DoSSimulationPanel from "../components/soc/DoSSimulationPanel";
import LiveAttackMapPanel from "../components/soc/LiveAttackMapPanel";
import ThreatActivityPanel from "../components/soc/ThreatActivityPanel";
import AttackTypesPanel from "../components/soc/AttackTypesPanel";
import SystemHealthPanel from "../components/soc/SystemHealthPanel";
import RecentSecurityActivity from "../components/soc/RecentSecurityActivity";
import ThreatIntelligenceSources from "../components/soc/ThreatIntelligenceSources";
import GlobalThreatIntelligence from "../components/soc/GlobalThreatIntelligence";

function normalizeAttackList(payload) {
  if (Array.isArray(payload)) return payload;
  if (payload && Array.isArray(payload.data)) return payload.data;
  if (payload && Array.isArray(payload.attacks)) return payload.attacks;
  if (payload && Array.isArray(payload.items)) return payload.items;
  if (payload && Array.isArray(payload.results)) return payload.results;
  return [];
}

function attackKey(attack) {
  const id = attack?.id ?? attack?.attack_id;
  if (id !== undefined && id !== null && String(id).trim() !== "") {
    return `id:${id}`;
  }

  return [
    attack?.source_ip || "",
    attack?.destination_ip || "",
    attack?.attack_type || "",
    attack?.timestamp || attack?.created_at || attack?.detected_at || attack?.event_time || "",
  ].join("|");
}

function mergeAttacks(incoming, existing, max = 500) {
  const merged = [];
  const seen = new Set();

  [...incoming, ...existing].forEach((item) => {
    const key = attackKey(item);
    if (!seen.has(key)) {
      seen.add(key);
      merged.push(item);
    }
  });

  return merged.slice(0, max);
}

function mapSocketAttack(message) {
  if (!message) return null;

  if (message.event === "new_attack" || message.type === "new_attack") {
    return message.attack || message.data || message.item || message.payload || null;
  }

  if (message.source_ip || message.attack_type) {
    return message;
  }

  return null;
}

function getSeverityCount(attacks, severity) {
  const value = String(severity).toLowerCase();
  return attacks.filter((item) => String(item?.severity || "low").toLowerCase() === value).length;
}

function toShortNumber(value) {
  return Number(value || 0).toLocaleString();
}

function KpiCard({ title, value, subtitle, icon: Icon, tone = "cyan" }) {
  const toneClass =
    tone === "red"
      ? "text-red-300 border-red-500/30"
      : tone === "amber"
      ? "text-amber-300 border-amber-500/30"
      : tone === "green"
      ? "text-green-300 border-green-500/30"
      : "text-cyan-300 border-cyan-500/30";

  return (
    <div className="rounded-lg border border-slate-800 bg-[#071a2f] p-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-[11px] uppercase tracking-wide text-slate-400">{title}</p>
          <p className={`mt-1 text-2xl font-semibold ${toneClass.split(" ")[0]}`}>{value}</p>
          <p className="mt-1 text-[11px] text-slate-500">{subtitle}</p>
        </div>
        <div className={`rounded-md border bg-slate-900/70 p-2 ${toneClass}`}>
          <Icon size={15} />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage({ profile, onLogout }) {
  const [attacks, setAttacks] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [apiHealthy, setApiHealthy] = useState(false);

  const mountedRef = useRef(true);
  const pollInFlightRef = useRef(false);

  const loadAttacks = useCallback(async () => {
    if (pollInFlightRef.current) return;

    pollInFlightRef.current = true;
    try {
      const response = await getAttacksApi(300);
      const rows = normalizeAttackList(response?.data ?? response);

      if (mountedRef.current) {
        setAttacks((current) => mergeAttacks(rows, current));
      }
    } catch {
      // keep existing state when polling fails
    } finally {
      pollInFlightRef.current = false;
    }
  }, []);

  const loadHealth = useCallback(async () => {
    try {
      await healthApi();
      if (mountedRef.current) setApiHealthy(true);
    } catch {
      if (mountedRef.current) setApiHealthy(false);
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    void loadAttacks();
    void loadHealth();

    const pollTimer = setInterval(() => {
      void loadAttacks();
    }, 5000);

    const healthTimer = setInterval(() => {
      void loadHealth();
    }, 30000);

    return () => {
      mountedRef.current = false;
      clearInterval(pollTimer);
      clearInterval(healthTimer);
    };
  }, [loadAttacks, loadHealth]);

  useEffect(() => {
    const disconnect = connectAttackSocket({
      onOpen: () => setWsConnected(true),
      onClose: () => setWsConnected(false),
      onMessage: (message) => {
        const nextAttack = mapSocketAttack(message);
        if (!nextAttack) return;

        setAttacks((current) => mergeAttacks([nextAttack], current));
      },
    });

    return () => {
      disconnect?.();
    };
  }, []);

  const totalEvents = attacks.length;
  const criticalAlerts = getSeverityCount(attacks, "critical");
  const highAlerts = getSeverityCount(attacks, "high");

  const blockedIps = useMemo(() => {
    const unique = new Set();
    attacks.forEach((item) => {
      const action = String(item?.action_taken || "").toLowerCase();
      if (action.includes("block") && item?.source_ip) {
        unique.add(item.source_ip);
      }
    });
    return unique.size;
  }, [attacks]);

  const activeThreats = useMemo(
    () =>
      attacks.filter((item) => {
        const status = String(item?.status || "active").toLowerCase();
        return !status.includes("resolved") && !status.includes("closed") && !status.includes("blocked");
      }).length,
    [attacks]
  );

  const automatedResponses = useMemo(
    () => attacks.filter((item) => /auto|automated/i.test(String(item?.action_taken || ""))).length,
    [attacks]
  );

  const avgRisk = useMemo(() => {
    if (attacks.length === 0) return 0;
    const total = attacks.reduce((sum, item) => sum + Number(item?.risk_score || 0), 0);
    return Math.round(total / attacks.length);
  }, [attacks]);

  const threatIntelMatches = useMemo(
    () => attacks.filter((item) => Number(item?.risk_score || 0) >= 85).length,
    [attacks]
  );

  const attackTypesData = useMemo(() => {
    const map = new Map();
    attacks.forEach((item) => {
      const type = item?.attack_type || "Unknown";
      map.set(type, (map.get(type) || 0) + 1);
    });

    return [...map.entries()]
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 6);
  }, [attacks]);

  const threatDistribution = useMemo(
    () => [
      { name: "Critical", value: criticalAlerts, color: "#ef4444" },
      { name: "High", value: highAlerts, color: "#f97316" },
      { name: "Medium", value: getSeverityCount(attacks, "medium"), color: "#eab308" },
      { name: "Low", value: getSeverityCount(attacks, "low"), color: "#22d3ee" },
    ],
    [attacks, criticalAlerts, highAlerts]
  );

  const recentAttacks = useMemo(() => attacks.slice(0, 20), [attacks]);

  const kpis = [
    { title: "Total Events", value: toShortNumber(totalEvents), subtitle: "Security events detected", icon: Activity },
    { title: "Active Threats", value: toShortNumber(activeThreats), subtitle: "Open active threats", icon: ShieldAlert, tone: "red" },
    { title: "Critical Alerts", value: toShortNumber(criticalAlerts), subtitle: "Immediate response queue", icon: AlertTriangle, tone: "amber" },
    { title: "Blocked IPs", value: toShortNumber(blockedIps), subtitle: "Firewall enforcement", icon: ShieldCheck, tone: "green" },
    { title: "High Severity", value: toShortNumber(highAlerts), subtitle: "High risk detections", icon: Radar, tone: "amber" },
    { title: "Avg Risk Score", value: `${avgRisk}`, subtitle: "Current risk baseline", icon: Target },
    { title: "Intel Matches", value: toShortNumber(threatIntelMatches), subtitle: "Indicator correlations", icon: Shield },
    { title: "Automated Actions", value: toShortNumber(automatedResponses), subtitle: "Auto response triggered", icon: Bot, tone: "green" },
  ];

  return (
    <PageShell profile={profile} onLogout={onLogout} title="SOC Dashboard">
      <div className="mx-auto max-w-[1600px] space-y-3">
        <section className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-4">
          {kpis.map((kpi) => (
            <KpiCard key={kpi.title} {...kpi} />
          ))}
        </section>

        <section className="grid grid-cols-1 gap-3 xl:grid-cols-12">
          <div className="space-y-3 xl:col-span-8">
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
              <DoSSimulationPanel />
              <LiveAttackMapPanel attacks={attacks} />
            </div>

            <RecentSecurityActivity attacks={recentAttacks} />

            <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
              <ThreatIntelligenceSources attacks={attacks} />
              <GlobalThreatIntelligence attacks={attacks} />
            </div>
          </div>

          <aside className="space-y-3 xl:col-span-4">
            <ThreatActivityPanel data={threatDistribution} total={totalEvents} />
            <AttackTypesPanel data={attackTypesData} />
            <SystemHealthPanel attacks={attacks} wsConnected={wsConnected} apiHealthy={apiHealthy} />
          </aside>
        </section>
      </div>
    </PageShell>
  );
}
