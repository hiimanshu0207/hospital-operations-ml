import React from 'react'
import { AlertTriangleIcon, RefreshCwIcon } from './Icons'

export default function ErrorAlert({
  title = 'Failed to load telemetry',
  message,
  onRetry,
  className = '',
}) {
  return (
    <div
      className={`rounded-2xl border border-rose-500/30 bg-gradient-to-r from-rose-500/10 via-slate-900/90 to-slate-900/90 p-5 backdrop-blur-md shadow-lg ${className}`}
    >
      <div className="flex items-start gap-3.5">
        <div className="p-2 rounded-xl bg-rose-500/20 text-rose-400 shrink-0 mt-0.5">
          <AlertTriangleIcon className="w-5 h-5" />
        </div>
        <div className="space-y-1.5 flex-1 min-w-0">
          <h4 className="font-semibold text-rose-300 text-sm tracking-wide">{title}</h4>
          <p className="text-xs text-rose-200/80 leading-relaxed break-words">{message}</p>

          {onRetry && (
            <div className="pt-2">
              <button
                type="button"
                onClick={onRetry}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 text-xs font-medium border border-rose-500/30 transition-colors"
              >
                <RefreshCwIcon className="w-3.5 h-3.5" />
                Retry Request
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
