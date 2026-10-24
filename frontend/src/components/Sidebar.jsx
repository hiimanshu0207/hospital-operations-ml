import React from 'react'
import {
  ActivityIcon,
  BuildingIcon,
  TrendingUpIcon,
  ClockIcon,
  SlidersIcon,
  UsersIcon,
} from './Icons'

const NAVIGATION_ITEMS = [
  {
    id: 'overview',
    label: 'Overview',
    description: 'Hospital KPIs & Telemetry',
    icon: ActivityIcon,
    color: 'text-cyan-400',
    activeBg: 'bg-cyan-500/15 border-cyan-500/40 text-cyan-300',
  },
  {
    id: 'departments',
    label: 'Departments',
    description: 'Beds, Staff & Queue Ratios',
    icon: BuildingIcon,
    color: 'text-blue-400',
    activeBg: 'bg-blue-500/15 border-blue-500/40 text-blue-300',
  },
  {
    id: 'forecast',
    label: 'Demand Forecast',
    description: 'Patient Inflow Trajectory',
    icon: TrendingUpIcon,
    color: 'text-indigo-400',
    activeBg: 'bg-indigo-500/15 border-indigo-500/40 text-indigo-300',
  },
  {
    id: 'waiting-time',
    label: 'Wait-Time Predictor',
    description: 'Triage Waiting Duration',
    icon: ClockIcon,
    color: 'text-amber-400',
    activeBg: 'bg-amber-500/15 border-amber-500/40 text-amber-300',
  },
  {
    id: 'simulation',
    label: 'What-If Simulation',
    description: 'Surge & Resource Scenarios',
    icon: SlidersIcon,
    color: 'text-rose-400',
    activeBg: 'bg-rose-500/15 border-rose-500/40 text-rose-300',
  },
  {
    id: 'allocation',
    label: 'Staff Allocation',
    description: 'Constrained Staff Optimizer',
    icon: UsersIcon,
    color: 'text-emerald-400',
    activeBg: 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300',
  },
]

export default function Sidebar({ activeTab, onTabChange }) {
  return (
    <aside className="w-full lg:w-64 shrink-0">
      <nav className="flex lg:flex-col gap-1.5 overflow-x-auto lg:overflow-x-visible pb-2 lg:pb-0 scrollbar-none">
        {NAVIGATION_ITEMS.map((item) => {
          const isActive = activeTab === item.id
          const Icon = item.icon
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onTabChange(item.id)}
              className={`flex items-center gap-3 px-3.5 py-3 rounded-xl text-left font-medium text-xs sm:text-sm transition-all duration-200 border whitespace-nowrap lg:whitespace-normal shrink-0 lg:shrink ${
                isActive
                  ? `${item.activeBg} shadow-md`
                  : 'bg-slate-900/40 hover:bg-slate-900/80 border-slate-800/80 text-slate-400 hover:text-slate-200'
              }`}
            >
              <div
                className={`p-2 rounded-lg shrink-0 ${
                  isActive ? 'bg-white/10 text-white' : 'bg-slate-800/80 text-slate-400'
                }`}
              >
                <Icon className="w-4 h-4" />
              </div>

              <div className="min-w-0">
                <p className="font-semibold leading-tight">{item.label}</p>
                <p className="hidden lg:block text-[11px] text-slate-500 font-normal truncate mt-0.5">
                  {item.description}
                </p>
              </div>
            </button>
          )
        })}
      </nav>
    </aside>
  )
}
