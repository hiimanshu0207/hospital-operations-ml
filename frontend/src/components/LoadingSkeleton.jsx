import React from 'react'

export function CardSkeleton({ count = 4 }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-3 animate-pulse"
        >
          <div className="flex justify-between items-center">
            <div className="h-3 w-24 bg-slate-800 rounded" />
            <div className="h-8 w-8 bg-slate-800 rounded-xl" />
          </div>
          <div className="h-8 w-20 bg-slate-800 rounded" />
          <div className="h-3 w-32 bg-slate-800/80 rounded" />
        </div>
      ))}
    </div>
  )
}

export function TableSkeleton({ rows = 5 }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4 animate-pulse">
      <div className="h-4 w-40 bg-slate-800 rounded" />
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex gap-4">
            <div className="h-4 w-1/4 bg-slate-800 rounded" />
            <div className="h-4 w-1/4 bg-slate-800/80 rounded" />
            <div className="h-4 w-1/4 bg-slate-800/60 rounded" />
            <div className="h-4 w-1/4 bg-slate-800/40 rounded" />
          </div>
        ))}
      </div>
    </div>
  )
}

export function ChartSkeleton() {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4 animate-pulse">
      <div className="flex justify-between items-center">
        <div className="h-4 w-48 bg-slate-800 rounded" />
        <div className="h-4 w-24 bg-slate-800 rounded" />
      </div>
      <div className="h-64 bg-slate-850/50 rounded-xl flex items-center justify-center">
        <div className="flex items-center gap-2 text-slate-500 text-sm">
          <div className="w-2.5 h-2.5 rounded-full bg-cyan-500 animate-ping" />
          Computing forecast trajectory...
        </div>
      </div>
    </div>
  )
}

export default function LoadingSpinner({ text = 'Loading operational telemetry...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 space-y-3 text-slate-400">
      <div className="relative w-10 h-10">
        <div className="absolute inset-0 rounded-full border-2 border-cyan-500/20" />
        <div className="absolute inset-0 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
      </div>
      <p className="text-sm font-medium text-slate-300">{text}</p>
    </div>
  )
}
