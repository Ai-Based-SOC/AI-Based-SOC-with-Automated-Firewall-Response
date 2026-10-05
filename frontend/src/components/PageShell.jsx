import { useState } from "react";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

export default function PageShell({
  title = "AI SOC",
  profile,
  onLogout,
  children,
}) {
  const [mobileSidebarOpen, setMobileSidebarOpen] =
    useState(false);

  function closeSidebar() {
    setMobileSidebarOpen(false);
  }

  return (
    <div className="min-h-screen overflow-x-hidden bg-[#020b1c] text-slate-100">
      {mobileSidebarOpen && (
        <button
          type="button"
          aria-label="Close sidebar"
          onClick={closeSidebar}
          className="fixed inset-0 z-40 bg-black/70 lg:hidden"
        />
      )}

      <Sidebar
        open={mobileSidebarOpen}
        onClose={closeSidebar}
      />

      <div className="min-h-screen lg:pl-[238px]">
        <TopBar
          title={title}
          profile={profile}
          onLogout={onLogout}
          onMenuClick={() => setMobileSidebarOpen(true)}
        />

        <main className="min-h-[calc(100vh-64px)] bg-[#020b1c] p-3 md:p-5 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}