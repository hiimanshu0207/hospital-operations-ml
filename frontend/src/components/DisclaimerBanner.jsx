import React from 'react'
import { ShieldCheckIcon, InfoIcon } from './Icons'

export default function DisclaimerBanner({
  text,
  title = 'Synthetic Data & Clinical Advisory',
  className = '',
  compact = false,
}) {
  const disclaimerMessage =
    text ||
    'NOTICE: This dashboard and its ML predictions are powered by synthetic healthcare data generated for academic research and clinical workflow optimization. Predictions represent statistical estimates, not real-world diagnosis or confirmed operational outcomes.'

  if (compact) {
    return (
      <div
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs ${className}`}
      >
        <InfoIcon className="w-4 h-4 shrink-0 text-amber-400" />
        <span className="truncate">{disclaimerMessage}</span>
      </div>
    )
  }

  return (
    <div
      className={`rounded-xl bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-slate-900/40 border border-amber-500/20 p-4 text-xs text-amber-200/90 shadow-sm backdrop-blur-sm ${className}`}
    >
      <div className="flex items-start gap-3">
        <div className="p-1.5 rounded-lg bg-amber-500/20 text-amber-400 shrink-0 mt-0.5">
          <ShieldCheckIcon className="w-4 h-4" />
        </div>
        <div className="space-y-1">
          <h4 className="font-semibold text-amber-300 tracking-wide uppercase text-[11px]">
            {title}
          </h4>
          <p className="leading-relaxed text-amber-200/80">{disclaimerMessage}</p>
        </div>
      </div>
    </div>
  )
}
