import { useState } from "react";
import { Play, ShieldAlert } from "lucide-react";
import Panel from "../Panel";
import { triggerDosSimulationApi } from "../../services/api";

const DEFAULT_PAYLOAD = {
  type: "dos_test",
  duration: 30,
  description: "Controlled DoS simulation training event",
};

export default function DoSSimulationPanel() {
  const [state, setState] = useState({ running: false, status: "idle", message: "Simulation is safe mode only." });

  const onRunSimulation = async () => {
    setState({ running: true, status: "running", message: "Submitting synthetic simulation request..." });

    try {
      const response = await triggerDosSimulationApi(DEFAULT_PAYLOAD);
      const message =
        response?.data?.message ||
        response?.data?.banner ||
        "Synthetic simulation completed. No real traffic generated.";
      setState({ running: false, status: "success", message });
    } catch {
      setState({
        running: false,
        status: "safe",
        message: "Simulation endpoint unavailable. Dashboard remains in safe synthetic mode.",
      });
    }
  };

  const statusClass =
    state.status === "success"
      ? "text-green-300 border-green-500/30 bg-green-500/10"
      : state.status === "running"
      ? "text-cyan-200 border-cyan-500/30 bg-cyan-500/10"
      : "text-amber-200 border-amber-500/30 bg-amber-500/10";

  return (
    <Panel title="DoS Simulation" className="bg-[#071a2f] border-cyan-900/60">
      <p className="text-xs text-slate-300">Run controlled backend simulation events for SOC validation.</p>
      <p className="mt-2 text-[11px] text-cyan-300">No browser-generated attack traffic is ever created.</p>

      <button
        type="button"
        onClick={onRunSimulation}
        disabled={state.running}
        className="mt-4 inline-flex items-center gap-2 rounded-md border border-cyan-500/40 bg-cyan-500/20 px-3 py-2 text-xs text-cyan-100 hover:bg-cyan-500/30 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <Play size={14} />
        {state.running ? "Running simulation..." : "Run synthetic simulation"}
      </button>

      <div className={`mt-4 flex items-start gap-2 rounded-md border px-3 py-2 text-xs ${statusClass}`}>
        <ShieldAlert size={14} className="mt-0.5 shrink-0" />
        <span>{state.message}</span>
      </div>
    </Panel>
  );
}
