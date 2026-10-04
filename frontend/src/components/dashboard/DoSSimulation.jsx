import React, { useState, useEffect } from "react";

export function DoSSimulation() {
  const [status, setStatus] = useState("ready");
  const [running, setRunning] = useState(false);

  const simulateDos = async () => {
    setStatus("running");
    setRunning(true);
    
    try {
      const response = await fetch("/api/v1/simulation/dos", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          type: "dos_test",
          duration: 30,
          description: "Controlled DoS simulation for SOC testing"
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        setStatus("completed");
        setRunning(false);
        // Could trigger refresh of dashboard data here
      } else {
        setStatus("failed");
        setRunning(false);
      }
    } catch (error) {
      setStatus("failed");
      setRunning(false);
    }
  };

  return (
    <div>
      <div className="alert alert-info soc-alert mb-4">
        <span className="icon"><ShieldAlert size={16} /></span>
        <strong>DoS Simulation:</strong> Controlled test attack for SOC detection capabilities.
      </div>
      
      {status === "ready" && (
        <button onClick={simulateDos} className="soc-btn soc-btn-primary w-full py-2 px-4 rounded-md text-sm font-medium text-white bg-cyan-600 hover:bg-cyan-500 transition-colors">
          Simulate DoS Attack
        </button>
      )}
      
      {status === "running" && (
        <div className="mt-3 p-3 bg-[#0d1a26] rounded-lg">
          <p className="text-slate-400 text-sm">Simulation running...</p>
          <div className="w-full bg-slate-800 rounded-h full-height mt-2">
            <div className="bg-cyan-600 h-full rounded-full rounded-l bg-gradient-to-r from-cyan-500 to-blue-500 border border-slate-700/50" style={{ width: '0%', transition: 'width 1s ease' }}></div>
          </div>
        </div>
      )}
      
      {status === "completed" && (
        <div className="mt-3 p-3 bg rgba(16, 185, 129, 0.1) rounded-lg border-green-600/50">
          <p className="text-green-400 text-sm">Simulation completed successfully</p>
          <p className="text-slate-400 text-xs mt-1">Test event generated and detected through the pipeline</p>
        </div>
      )}
      
      {status === "failed" && (
        <div className="mt-3 p-3 bg-red-600/10 rounded-lg border-red-500/50">
          <p className="text-red-400 text-sm">Simulation failed</p>
          <p className="text-slate-400 text-xs mt-1">Please try again or check backend status</p>
        </div>
      )}
    </div>
  );
}