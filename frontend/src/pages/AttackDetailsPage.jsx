import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import PageShell from "../components/PageShell";
import Panel from "../components/Panel";
import { getAttackApi } from "../services/api";

export default function AttackDetailsPage({ profile, onLogout }) {
  const { attackId } = useParams();
  const [attack, setAttack] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const response = await getAttackApi(attackId);
        if (active) setAttack(response.data);
      } catch {
        if (active) setError("Attack details could not be loaded.");
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [attackId]);

  return (
    <PageShell
      title="Attack Details"
      profile={profile}
      onLogout={onLogout}
    >
      <div className="mx-auto max-w-[1400px] space-y-4">
        <Link
          to="/logs"
          className="text-sm text-cyan-300 hover:text-cyan-100"
        >
          ← Back to Attack Logs
        </Link>

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-red-300">
            {error}
          </div>
        )}

        {attack && (
          <>
            <Panel title={attack.attack_type || "Security Incident"}>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div>
                  <p className="text-xs text-slate-500">Source IP</p>
                  <p className="font-mono text-cyan-300">
                    {attack.source_ip || "--"}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">Destination IP</p>
                  <p className="font-mono text-cyan-300">
                    {attack.destination_ip || "--"}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">Severity</p>
                  <p className="capitalize text-red-300">
                    {attack.severity || "low"}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">Risk Score</p>
                  <p className="text-white">{attack.risk_score ?? "--"}</p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">Action</p>
                  <p className="text-green-300">
                    {attack.action_taken || "Detected"}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">Location</p>
                  <p className="text-slate-300">
                    {attack.country || attack.location || "Unknown"}
                  </p>
                </div>
              </div>
            </Panel>

            <Panel title="Detection Reason">
              <p className="text-sm leading-7 text-slate-300">
                {attack.reason || attack.description || "No reason provided."}
              </p>
            </Panel>

            <Panel title="Timeline">
              <div className="space-y-3 text-sm text-slate-300">
                <p>Event received</p>
                <p>Threat analysis completed</p>
                <p>Firewall response recorded</p>
              </div>
            </Panel>
          </>
        )}
      </div>
    </PageShell>
  );
}