import React from 'react'
import DisclaimerBanner from '../components/DisclaimerBanner'
import { CardSkeleton } from '../components/LoadingSkeleton'
import ErrorAlert from '../components/ErrorAlert'
import {
  BuildingIcon,
  BedIcon,
  UsersIcon,
  ClockIcon,
  AlertTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '../components/Icons'

export default function DepartmentsTab({
  utilizationData,
  loading,
  error,
  onRefresh,
}) {
  if (loading && !utilizationData) {
    return (
      <div className="space-y-6">
        <CardSkeleton count={4} />
      </div>
    )
  }

  if (error && !utilizationData) {
    return (
      <ErrorAlert
        title="Failed to load department operational metrics"
        message={error}
        onRetry={onRefresh}
      />
    )
  }

  const departments = utilizationData?.department_utilization || []

  if (departments.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-12 text-center text-slate-400 space-y-3">
        <BuildingIcon className="w-10 h-10 mx-auto text-slate-600" />
        <h3 className="text-base font-semibold text-slate-200">No Departments Found</h3>
        <p className="text-xs max-w-sm mx-auto text-slate-500">
          The database currently has no department operational records. Initialize or seed synthetic data.
        </p>
      </div>
    )
  }

  const pressureBadgeMap = {
    Low: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    Moderate: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
    High: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    Severe: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">
            Department Operations &amp; Resource Status
          </h2>
          <p className="text-xs text-slate-400">
            Real-time monitoring of bed capacity, staffing ratios, queue pressures, and wait times
          </p>
        </div>
        <span className="text-xs font-mono text-cyan-400 bg-cyan-500/10 px-3 py-1 rounded-full border border-cyan-500/20 w-fit">
          {departments.length} Clinical Units
        </span>
      </div>

      {/* Grid of Department Cards */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        {departments.map((dept) => {
          const bed = dept.bed_capacity
          const staff = dept.staffing
          const queue = dept.queue_and_demand
          const wait = dept.estimated_wait_time

          const utilRate = bed.utilization_rate_pct || 0
          const isCriticalBed = utilRate >= 95
          const isHighBed = utilRate >= 85

          const barColor = isCriticalBed
            ? 'bg-rose-500'
            : isHighBed
            ? 'bg-amber-500'
            : 'bg-cyan-500'

          return (
            <div
              key={dept.department_code}
              className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-4 shadow-lg backdrop-blur-md transition-all duration-200 hover:border-slate-700"
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-3 border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-600 to-blue-700 flex items-center justify-center text-white font-bold text-sm shadow">
                    {dept.department_code}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">{dept.department_name}</h3>
                    <span className="text-[11px] text-slate-400 font-mono">
                      Code: {dept.department_code}
                    </span>
                  </div>
                </div>

                {/* Queue Pressure Badge */}
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold border ${
                      pressureBadgeMap[queue.queue_pressure_level] || pressureBadgeMap.Low
                    }`}
                  >
                    Queue: {queue.queue_pressure_level}
                  </span>
                </div>
              </div>

              {/* 3-Column Metrics Breakdown */}
              <div className="grid grid-cols-3 gap-3">
                {/* Bed Capacity */}
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
                  <div className="flex items-center gap-1.5 text-slate-400 text-xs">
                    <BedIcon className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Beds</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-baseline justify-between">
                      <span className="text-lg font-bold text-white">
                        {utilRate.toFixed(1)}%
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {bed.occupied_beds}/{bed.total_beds}
                      </span>
                    </div>
                    {/* Progress Bar */}
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${barColor}`}
                        style={{ width: `${Math.min(utilRate, 100)}%` }}
                      />
                    </div>
                  </div>
                  <p className="text-[10px] text-slate-500 font-mono">
                    {bed.available_beds} beds free
                  </p>
                </div>

                {/* Staffing & Nurse Ratio */}
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
                  <div className="flex items-center gap-1.5 text-slate-400 text-xs">
                    <UsersIcon className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Staff Census</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-baseline justify-between">
                      <span className="text-lg font-bold text-white">
                        {staff.active_staff_total}
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {staff.nurse_count} nurses
                      </span>
                    </div>
                    <div className="flex items-center gap-1 text-[11px]">
                      {staff.ratio_compliant ? (
                        <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                          <CheckCircleIcon className="w-3 h-3" /> Compliant
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-rose-400 font-medium">
                          <XCircleIcon className="w-3 h-3" /> Understaffed
                        </span>
                      )}
                    </div>
                  </div>
                  <p className="text-[10px] text-slate-500 font-mono">
                    Req: {staff.required_nurses_for_census} nurses
                  </p>
                </div>

                {/* Queue & ML Wait Time */}
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
                  <div className="flex items-center gap-1.5 text-slate-400 text-xs">
                    <ClockIcon className="w-3.5 h-3.5 text-amber-400" />
                    <span>Est. Wait (ESI-3)</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-baseline justify-between">
                      <span className="text-lg font-bold text-amber-300">
                        {wait.estimated_minutes?.toFixed(1)}
                        <span className="text-xs font-normal text-slate-400 ml-0.5">m</span>
                      </span>
                      <span className="text-[11px] text-slate-400">
                        Queue: {queue.current_queue_estimate}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">
                      Q/Staff: {queue.queue_to_staff_ratio?.toFixed(2)}
                    </p>
                  </div>
                  <p className="text-[10px] text-cyan-400/90 font-mono flex items-center gap-1">
                    <span className="w-1 h-1 rounded-full bg-cyan-400" />
                    ML Model Est.
                  </p>
                </div>
              </div>

              {/* Department Warnings if any */}
              {dept.warnings && dept.warnings.length > 0 && (
                <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200/90 space-y-1">
                  <div className="flex items-center gap-1.5 text-amber-400 font-semibold text-[11px]">
                    <AlertTriangleIcon className="w-3.5 h-3.5" />
                    <span>Department Warnings ({dept.warnings.length})</span>
                  </div>
                  <ul className="space-y-0.5 pl-4 list-disc text-[11px] text-amber-200/80">
                    {dept.warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Synthetic Data Disclaimer */}
      <DisclaimerBanner text={utilizationData?.disclaimer} />
    </div>
  )
}
