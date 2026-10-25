import React from 'react'
import { ActivityIcon, RefreshCwIcon, ShieldCheckIcon } from './Icons'

export default function Navbar({
  backendStatus = 'connecting', // connected, offline, connecting
  lastUpdated,
  onRefresh,
  isRefreshing = false,
}) {
  const statusConfig = {
    connected: {
      color: 'bg-emerald-500',
      text: 'text-emerald-400',
      border: 'border-emerald-500/30',
      bg: 'bg-emerald-500/10',
      label: 'API Online',
    },
    offline: {
      color: 'bg-rose-500',
      text: 'text-rose-400',
      border: 'border-rose-500/30',
      bg: 'bg-rose-500/10',
      label: 'API Offline',
    },
    connecting: {
      color: 'bg-amber-400',
      text: 'text-amber-400',
      border: 'border-amber-500/30',
      bg: 'bg-amber-500/10',
      label: 'Connecting...',
    },
  }

  const currentStatus = statusConfig[backendStatus] || statusConfig.connecting

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-cyan-500/20 ring-1 ring-white/20">
            <ActivityIcon className="w-5 h-5 text-cyan-100" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base sm:text-lg font-bold tracking-tight text-white">
                Hospital<span className="text-cyan-400">Ops</span>
              </h1>
              <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 tracking-wider">
                ML Decision Support
              </span>
            </div>
            <p className="hidden sm:block text-xs text-slate-400">
              Workflow &amp; Capacity Optimization
            </p>
          </div>
        </div>

        {/* Right side controls & status */}
        <div className="flex items-center gap-3 sm:gap-4">
          {/* Synthetic Data badge */}
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-[11px] text-slate-400">
            <ShieldCheckIcon className="w-3.5 h-3.5 text-cyan-400" />
            <span>Synthetic Clinical Operations</span>
          </div>

          {/* Backend Status indicator */}
          <div
            className={`flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium border ${currentStatus.bg} ${currentStatus.border} ${currentStatus.text}`}
          >
            <span
              className={`w-2 h-2 rounded-full ${currentStatus.color} ${
                backendStatus === 'connecting' ? 'animate-ping' : ''
              }`}
            />
            <span>{currentStatus.label}</span>
          </div>

          {/* Refresh button */}
          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              disabled={isRefreshing}
              title="Refresh operational telemetry"
              className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition-all duration-200 active:scale-95 disabled:opacity-50"
            >
              <RefreshCwIcon className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
            </button>
          )}

          {/* Timestamp */}
          {lastUpdated && (
            <span className="hidden lg:block text-xs text-slate-500 font-mono">
              {new Date(lastUpdated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
          )}
        </div>
      </div>
    </header>
  )
}
