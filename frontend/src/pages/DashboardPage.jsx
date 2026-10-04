<PageShell profile={profile} onLogout={onLogout}>
  <main className="min-h-screen bg-[#020b1c] p-3 text-white md:p-4">
    <div className="mx-auto max-w-[1600px]">
      {/* Page heading */}
      <div className="mb-3 flex flex-col justify-between gap-3 lg:flex-row lg:items-center">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-white md:text-2xl">
              Security Operations Center
            </h1>

            <span className="rounded-full border border-green-500/30 bg-green-500/10 px-2 py-0.5 text-[10px] font-semibold text-green-400">
              <span className="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-green-400" />
              LIVE
            </span>
          </div>

          <p className="text-[10px] text-cyan-300">
            Real-time security monitoring and automated threat response
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select className="rounded-md border border-cyan-700 bg-[#061a32] px-3 py-1.5 text-[10px] text-slate-200">
            <option>Live</option>
            <option>24 Hours</option>
            <option>7 Days</option>
            <option>30 Days</option>
          </select>

          <span className="rounded-md border border-green-500/30 bg-green-500/10 px-3 py-1.5 text-[10px] text-green-400">
            ● System Operational
          </span>
        </div>
      </div>

      {/* KPI grid */}
      <section className="mb-3 grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="TOTAL EVENTS"
          value={totalEvents.toLocaleString()}
          subtitle="Security events detected"
          icon="◉"
          valueClass="text-cyan-400"
          trend="+12%"
          trendClass="text-green-400"
        />

        <MetricCard
          title="ACTIVE THREATS"
          value={activeThreats.toLocaleString()}
          subtitle="Currently active threats"
          icon="⚠"
          valueClass="text-red-400"
          trend="+35%"
          trendClass="text-red-400"
        />

        <MetricCard
          title="CRITICAL ALERTS"
          value={criticalAlerts.toLocaleString()}
          subtitle="Immediate attention required"
          icon="!"
          valueClass="text-orange-400"
          trend="+75%"
          trendClass="text-red-400"
        />

        <MetricCard
          title="BLOCKED IPS"
          value={blockedIps.toLocaleString()}
          subtitle="Firewall response actions"
          icon="🛡"
          valueClass="text-cyan-400"
          trend="+22%"
          trendClass="text-green-400"
        />

        <MetricCard
          title="ACTIVE INCIDENTS"
          value={activeIncidents.toLocaleString()}
          subtitle="Open security incidents"
          icon="◈"
          valueClass="text-purple-400"
          trend="+67%"
          trendClass="text-red-400"
        />

        <MetricCard
          title="ASSETS MONITORED"
          value="247"
          subtitle="Windows SOC assets"
          icon="♟"
          valueClass="text-cyan-400"
          trend="+2%"
          trendClass="text-green-400"
        />

        <MetricCard
          title="THREAT INTEL MATCHES"
          value={threatIntelMatches.toLocaleString()}
          subtitle="Matched indicators"
          icon="◎"
          valueClass="text-purple-400"
          trend="+140%"
          trendClass="text-purple-400"
        />

        <MetricCard
          title="AUTOMATED RESPONSES"
          value={automatedResponses.toLocaleString()}
          subtitle="Automated SOC actions"
          icon="⚡"
          valueClass="text-yellow-400"
          trend="+48%"
          trendClass="text-green-400"
        />
      </section>

      {/* Main dashboard */}
      <section className="grid grid-cols-1 gap-2 xl:grid-cols-12">
        {/* Center content */}
        <div className="space-y-2 xl:col-span-8">
          <div className="grid grid-cols-1 gap-2 lg:grid-cols-2">
            <DoSSimulationPanel />

            <LiveAttackMapPanel
              attacks={filteredAttacks}
            />
          </div>

          <RecentSecurityActivity
            attacks={recentAttacks}
          />

          <div className="grid grid-cols-1 gap-2 lg:grid-cols-2">
            <ThreatIntelligenceSources />
            <GlobalThreatIntelligence />
          </div>
        </div>

        {/* Right content */}
        <aside className="space-y-2 xl:col-span-4">
          <ThreatActivityPanel
            data={threatDistribution}
            total={totalEvents}
          />

          <AttackTypesPanel
            data={attackTypesData}
          />

          <SystemHealthPanel
            attacks={recentAttacks}
          />
        </aside>
      </section>
    </div>
  </main>
</PageShell>