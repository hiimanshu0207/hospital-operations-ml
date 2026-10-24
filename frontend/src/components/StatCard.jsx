import React from 'react'

export default function StatCard({
  title,
  value,
  unit = '',
  subtitle,
  icon: Icon,
  color = 'cyan', // cyan, emerald, amber, rose, indigo, purple
  badge,
  badgeType = 'neutral', // success, warning, danger, neutral
}) {
  const colorMap = {
    cyan: {
      border: 'border-cyan-500/20 hover:border-cyan-500/40',
      bgGlow: 'from-cyan-500/10 to-transparent',
      iconBg: 'bg-cyan-500/20 text-cyan-400',
      textAccent: 'text-cyan-400',
    },
    emerald: {
      border: 'border-emerald-500/20 hover:border-emerald-500/40',
      bgGlow: 'from-emerald-500/10 to-transparent',
      iconBg: 'bg-emerald-500/20 text-emerald-400',
      textAccent: 'text-emerald-400',
    },
    amber: {
      border: 'border-amber-500/20 hover:border-amber-500/40',
      bgGlow: 'from-amber-500/10 to-transparent',
      iconBg: 'bg-amber-500/20 text-amber-400',
      textAccent: 'text-amber-400',
    },
    rose: {
      border: 'border-rose-500/20 hover:border-rose-500/40',
      bgGlow: 'from-rose-500/10 to-transparent',
      iconBg: 'bg-rose-500/20 text-rose-400',
      textAccent: 'text-rose-400',
    },
    indigo: {
      border: 'border-indigo-500/20 hover:border-indigo-500/40',
      bgGlow: 'from-indigo-500/10 to-transparent',
      iconBg: 'bg-indigo-500/20 text-indigo-400',
      textAccent: 'text-indigo-400',
    },
    purple: {
      border: 'border-purple-500/20 hover:border-purple-500/40',
      bgGlow: 'from-purple-500/10 to-transparent',
      iconBg: 'bg-purple-500/20 text-purple-400',
      textAccent: 'text-purple-400',
    },
  }

  const badgeMap = {
    success: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    warning: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    danger: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
    neutral: 'bg-slate-700/50 text-slate-300 border-slate-600/30',
  }

  const theme = colorMap[color] || colorMap.cyan

  return (
    <div
      className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${theme.bgGlow} via-slate-900/90 to-slate-900/60 p-5 border ${theme.border} backdrop-blur-md shadow-lg transition-all duration-300 hover:shadow-cyan-500/5 hover:-translate-y-0.5`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-400">{title}</p>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl md:text-3xl font-bold tracking-tight text-white">{value}</span>
            {unit && <span className="text-sm font-semibold text-slate-400">{unit}</span>}
          </div>
        </div>

        {Icon && (
          <div className={`p-2.5 rounded-xl ${theme.iconBg} shadow-inner`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      {(subtitle || badge) && (
        <div className="mt-3 flex items-center justify-between gap-2 pt-2 border-t border-slate-800/80 text-xs">
          {subtitle && <span className="text-slate-400 truncate">{subtitle}</span>}
          {badge && (
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-md font-medium text-[11px] border ${badgeMap[badgeType] || badgeMap.neutral}`}
            >
              {badge}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
