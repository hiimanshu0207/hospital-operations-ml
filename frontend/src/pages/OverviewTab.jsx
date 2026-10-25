import React, { useEffect, useState } from 'react'
import StatCard from '../components/StatCard'
import DisclaimerBanner from '../components/DisclaimerBanner'
import LoadingSpinner, { CardSkeleton, TableSkeleton } from '../components/LoadingSkeleton'
import ErrorAlert from '../components/ErrorAlert'
import {
  BedIcon,
  UsersIcon,
  ActivityIcon,
  AlertTriangleIcon,
  ClockIcon,
} from '../components/Icons'
import { getRecentVisits, getVisitsSummary, getErrorMessage } from '../services/api'

export default function OverviewTab({
  utilizationData,
  loadingUtilization,
  utilizationError,
  onRefresh,
}) {
  const [visitsSummary, setVisitsSummary] = useState(null)
  const [recentVisits, setRecentVisits] = useState([])
  const [loadingVisits, setLoadingVisits] = useState(true)
  const [visitsError, setVisitsError] = useState(null)

  useEffect(() => {
    let isMounted = true

    Promise.allSettled([getVisitsSummary(), getRecentVisits(8)])
      .then(([summaryResult, recentResult]) => {
        if (!isMounted) return

        let err = null
        if (summaryResult.status === 'fulfilled') {
          setVisitsSummary(summaryResult.value)
        } else {
          err = getErrorMessage(summaryResult.reason)
          setVisitsError(err)
        }

        if (recentResult.status === 'fulfilled') {
          setRecentVisits(recentResult.value || [])
        } else if (!err) {
          setVisitsError(getErrorMessage(recentResult.reason))
        }
      })
      .finally(() => {
        if (isMounted) setLoadingVisits(false)
      })

    return () => {
      isMounted = false
    }
  }, [])

  if (loadingUtilization && !utilizationData) {
    return (
      <div className="space-y-6">
        <CardSkeleton count={4} />
        <TableSkeleton rows={4} />
      </div>
    )
  }

  if (utilizationError && !utilizationData) {
    return (
      <ErrorAlert
        title="Failed to load hospital operational overview"
        message={utilizationError}
        onRetry={onRefresh}
      />
    )
  }

  const summary = utilizationData?.hospital_summary || {
    total_beds: 0,
    total_occupied_beds: 0,
    total_available_beds: 0,
    overall_bed_utilization_pct: 0.0,
    total_active_staff: 0,
    active_warning_count: 0,
    operational_stress_index: 0.0,
  }

  const stressIndex = summary.operational_stress_index || 0.0
  const stressLevel =
    stressIndex >= 70.0 ? 'Critical Stress' : stressIndex >= 40.0 ? 'Elevated Pressure' : 'Normal Operations'
  const stressBadgeType =
    stressIndex >= 70.0 ? 'danger' : stressIndex >= 40.0 ? 'warning' : 'success'
  const stressColor =
    stressIndex >= 70.0 ? 'rose' : stressIndex >= 40.0 ? 'amber' : 'emerald'

  const activeWarnings = utilizationData?.active_warnings || []
  const departments = utilizationData?.department_utilization || []

  const acuityColors = {
    1: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
    2: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
    3: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
    4: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
    5: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
  }

  return (
    <div className="space-y-6">
      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Bed Occupancy"
          value={`${summary.overall_bed_utilization_pct?.toFixed(1) || 0}%`}
          subtitle={`${summary.total_occupied_beds || 0} of ${summary.total_beds || 0} beds occupied`}
          icon={BedIcon}
          color={summary.overall_bed_utilization_pct > 85 ? 'rose' : 'cyan'}
          badge={`${summary.total_available_beds || 0} available`}
          badgeType={summary.total_available_beds < 5 ? 'danger' : 'neutral'}
        />

        <StatCard
          title="Active Staff Census"
          value={summary.total_active_staff || 0}
          unit="personnel"
          subtitle="Staff across all 3 shifts"
          icon={UsersIcon}
          color="indigo"
          badge="On Duty"
          badgeType="success"
        />

        <StatCard
          title="Operational Stress"
          value={`${stressIndex.toFixed(1)} / 100`}
          subtitle={stressLevel}
          icon={ActivityIcon}
          color={stressColor}
          badge={stressLevel}
          badgeType={stressBadgeType}
        />

        <StatCard
          title="Avg Triage Wait"
          value={
            typeof visitsSummary?.avg_waiting_time_minutes === 'number'
              ? `${visitsSummary.avg_waiting_time_minutes.toFixed(1)}`
              : '—'
          }
          unit={typeof visitsSummary?.avg_waiting_time_minutes === 'number' ? 'min' : ''}
          subtitle={`Total visits: ${visitsSummary?.total_visits ?? 0}`}
          icon={ClockIcon}
          color="amber"
          badge={
            summary.active_warning_count > 0
              ? `${summary.active_warning_count} active warnings`
              : 'No Alerts'
          }
          badgeType={summary.active_warning_count > 0 ? 'warning' : 'success'}
        />
      </div>

      {/* Operational Warnings Banner if any */}
      {activeWarnings.length > 0 && (
        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 space-y-2">
          <div className="flex items-center gap-2 text-amber-400 font-semibold text-xs tracking-wider uppercase">
            <AlertTriangleIcon className="w-4 h-4" />
            <span>Active Resource &amp; Capacity Warnings ({activeWarnings.length})</span>
          </div>
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-amber-200/90">
            {activeWarnings.map((warning, index) => (
              <li
                key={index}
                className="flex items-start gap-2 bg-slate-900/60 p-2.5 rounded-lg border border-amber-500/20"
              >
                <span className="text-amber-400 font-bold">•</span>
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Department Capacity Breakdown */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4 shadow-lg backdrop-blur-md">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <h3 className="text-sm font-semibold text-white tracking-wide">
              Departmental Bed Capacity &amp; Census
            </h3>
            <p className="text-xs text-slate-400">
              Real-time bed utilization across clinical units
            </p>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {departments.length} Units Monitored
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {departments.map((dept) => {
            const bedCap = dept.bed_capacity
            const rate = bedCap?.utilization_rate_pct || 0
            const isHigh = rate >= 85
            const isCritical = rate >= 95

            const barColor = isCritical
              ? 'bg-rose-500'
              : isHigh
              ? 'bg-amber-500'
              : 'bg-cyan-500'

            return (
              <div
                key={dept.department_code}
                className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2.5"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-white px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                      {dept.department_code}
                    </span>
                    <span className="text-xs font-medium text-slate-300 truncate max-w-[120px]">
                      {dept.department_name}
                    </span>
                  </div>
                  <span
                    className={`text-xs font-semibold ${
                      isCritical
                        ? 'text-rose-400'
                        : isHigh
                        ? 'text-amber-400'
                        : 'text-cyan-400'
                    }`}
                  >
                    {rate.toFixed(1)}%
                  </span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                    style={{ width: `${Math.min(rate, 100)}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span>
                    {bedCap.occupied_beds} / {bedCap.total_beds} beds occupied
                  </span>
                  <span>{bedCap.available_beds} free</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Recent Patient Visits Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4 shadow-lg backdrop-blur-md">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <h3 className="text-sm font-semibold text-white tracking-wide">
              Recent Patient Encounters
            </h3>
            <p className="text-xs text-slate-400">
              Latest synthetic clinical visits observed at triage
            </p>
          </div>
          <span className="text-xs text-cyan-400 font-medium">
            Live Encounter Stream
          </span>
        </div>

        {visitsError && (
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
            Encounter stream note: {visitsError}
          </div>
        )}

        {loadingVisits ? (
          <LoadingSpinner text="Retrieving recent encounters..." />
        ) : recentVisits.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-xs">
            No patient visits recorded in the current operational state.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400">
                  <th className="pb-2.5 font-medium">Encounter ID</th>
                  <th className="pb-2.5 font-medium">Age Group</th>
                  <th className="pb-2.5 font-medium">Acuity (ESI)</th>
                  <th className="pb-2.5 font-medium">Queue at Arrival</th>
                  <th className="pb-2.5 font-medium">Staff on Duty</th>
                  <th className="pb-2.5 font-medium">Wait Time</th>
                  <th className="pb-2.5 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {recentVisits.map((visit) => (
                  <tr key={visit.id || visit.visit_id} className="hover:bg-slate-800/40">
                    <td className="py-2.5 font-mono text-cyan-400 font-medium">
                      {visit.visit_id}
                    </td>
                    <td className="py-2.5">{visit.patient_age_group}</td>
                    <td className="py-2.5">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border ${
                          acuityColors[visit.acuity_level] || 'bg-slate-800 text-slate-300'
                        }`}
                      >
                        ESI {visit.acuity_level}
                      </span>
                    </td>
                    <td className="py-2.5">{visit.queue_length_at_arrival}</td>
                    <td className="py-2.5">{visit.staff_available_at_arrival}</td>
                    <td className="py-2.5 font-mono">
                      {visit.waiting_time_minutes?.toFixed(1)} min
                    </td>
                    <td className="py-2.5">
                      <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                        {visit.status || 'Completed'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Synthetic Data Disclaimer */}
      <DisclaimerBanner text={utilizationData?.disclaimer} />
    </div>
  )
}
