<aside className="fixed inset-y-0 left-0 z-50 w-[164px] border-r border-cyan-900/70 bg-[#03152b]">
  <div className="flex h-14 items-center gap-2 border-b border-cyan-900/70 px-3">
    <div className="flex h-7 w-7 items-center justify-center rounded-md bg-cyan-500 text-sm font-bold text-slate-950">
      ◇
    </div>

    <div>
      <p className="text-xs font-bold text-white">AI-SOC</p>
      <p className="text-[7px] text-cyan-300">
        AI Based Security Operations Center
      </p>
    </div>
  </div>

  <nav className="space-y-1 p-2">
    {navigation.map((item) => (
      <a
        key={item.label}
        href={item.href}
        className="flex items-center gap-2 rounded-md px-2 py-2 text-[10px] text-slate-300 transition hover:bg-blue-600/30 hover:text-white"
      >
        <span className="w-4 text-center text-sm">{item.icon}</span>
        <span>{item.label}</span>

        {item.badge && (
          <span className="ml-auto rounded-full bg-red-500 px-1.5 py-0.5 text-[8px]">
            4
          </span>
        )}
      </a>
    ))}
  </nav>

  <div className="absolute bottom-0 w-full border-t border-cyan-900/70 p-2">
    <div className="mb-2 flex items-center gap-2">
      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-500 text-[10px]">
        A
      </div>

      <div>
        <p className="text-[9px] text-white">admin</p>
        <p className="text-[8px] text-slate-500">Administrator</p>
      </div>
    </div>

    <button className="flex w-full items-center gap-2 px-1 py-2 text-[10px] text-slate-400 hover:text-white">
      ⇥ Logout
    </button>
  </div>
</aside>