import React from "react";
import { useState, useEffect } from "react";
import Sidebar from "./Sidebar";
import { TopBar } from "./TopBar";
import { useAuth } from "../hooks/useAuth";

export function AppShell({ children }) {
  const [systemStatus, setSystemStatus] = useState("online");
  const [notifications, setNotifications] = useState(0);

  useEffect(() => {
    const updateStatus = async () => {
      try {
        const { data } = await fetch("/api/status").then((r) => r.json());
        setSystemStatus(data.status || "online");
        setNotifications(data.notifications || 0);
      } catch {
        setSystemStatus("offline");
      }
    };
    updateStatus();
    const interval = setInterval(updateStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="soc-app">
      <TopBar systemStatus={systemStatus} notifications={notifications} />
      <Sidebar />
      <main className="soc-content">
        <div className="soc-main">{children}</div>
      </main>
    </div>
  );
}