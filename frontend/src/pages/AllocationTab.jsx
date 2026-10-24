import React, { useState, useEffect } from 'react'
import DisclaimerBanner from '../components/DisclaimerBanner'
import LoadingSpinner from '../components/LoadingSkeleton'
import ErrorAlert from '../components/ErrorAlert'
import StatCard from '../components/StatCard'
import {
  UsersIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  ActivityIcon,
  SparklesIcon,
} from '../components/Icons'
import { optimizeStaffAllocation, getErrorMessage } from '../services/api'

const SHIFTS = ['All', 'Morning', 'Evening', 'Night']

export default function AllocationTab() {
  const [selectedShift, setSelectedShift] = useState('All')
  const [staffBudget, setStaffBudget] = useState('')
  const [allocationResult, setAllocationResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const handleOptimize = (shift, budget) => {
    setLoading(true)
    setError(null)

    optimizeStaffAllocation({
      shift,
      total_staff_budget: budget !== '' && budget !== null && budget !== undefined ? Number(budget) : null,
    })
      .then((data) => {
        setAllocationResult(data)
      })
      .catch((err) => {
        setError(getErrorMessage(err))
      })
      .finally(() => {
        setLoading(false)
      })
  }

  // Load default allocation on mount
  useEffect(() => {
    let ignore = false
    optimizeStaffAllocation({ shift: 'All', total_staff_budget: null })
      .then((data) => {
        if (!ignore) setAllocationResult(data)
      })
      .catch((err) => {
        if (!ignore) setError(getErrorMessage(err))
      })
      .finally(() => {
        if (!ignore) setLoading(false)
      })
    return () => {
      ignore = true
    }
  }, [])

  const handleShiftChange = (shift) => {
    setSelectedShift(shift)
    handleOptimize(shift, staffBudget)
  }

  const recommendations = allocationResult?.recommendations || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-bold text-white tracking-tight">
          Hospital Staff Allocation Optimization
        </h2>
        <p className="text-xs text-slate-400">
          Linear programming optimization balancing patient census, clinical acuity priorities, and safety constraints
        </p>
      </div>

      {/* Control Panel */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-4 shadow-lg backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2">
            <UsersIcon className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-white">Optimization Parameters</h3>
          </div>
          <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            Linear Programming (SLSQP / Simplex)
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
          {/* Shift Selector */}
          <div className="md:col-span-5 space-y-1.5">
            <label className="text-xs font-medium text-slate-300">Target Shift</label>
            <div className="grid grid-cols-4 gap-1.5">
              {SHIFTS.map((shift) => (
                <button
                  key={shift}
                  type="button"
                  onClick={() => handleShiftChange(shift)}
                  className={`py-2 text-center rounded-xl text-xs font-medium transition-all border ${
                    selectedShift === shift
                      ? 'bg-emerald-500 text-slate-950 font-bold border-emerald-400 shadow'
                      : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white'
                  }`}
                >
                  {shift}
                </button>
              ))}
            </div>
          </div>

          {/* Budget Input */}
          <div className="md:col-span-4 space-y-1.5">
            <div className="flex justify-between items-center">
              <label className="text-xs font-medium text-slate-300">Staff Budget (Optional)</label>
              <button
                type="button"
                onClick={() => setStaffBudget('')}
                className="text-[10px] text-slate-500 hover:text-slate-300 underline"
              >
                Reset to Current Census
              </button>
            </div>
            <input
              type="number"
              min="5"
              max="300"
              placeholder="e.g. 84 (Current census)"
              value={staffBudget}
              onChange={(e) => setStaffBudget(e.target.value)}
              className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 font-mono"
            />
          </div>

          {/* Solve Button */}
          <div className="md:col-span-3">
            <button
              type="button"
              onClick={() => handleOptimize(selectedShift, staffBudget)}
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white font-semibold text-xs tracking-wide shadow-md shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <SparklesIcon className="w-4 h-4" />
              {loading ? 'Optimizing...' : 'Solve Staff Plan'}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <ErrorAlert
          title="Optimization failed"
          message={error}
          onRetry={() => handleOptimize(selectedShift, staffBudget)}
        />
      )}

      {loading && !allocationResult && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-12 text-center backdrop-blur-md">
          <LoadingSpinner text="Solving constrained optimization problem..." />
        </div>
      )}

      {allocationResult && (
        <>
          {/* Summary KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Optimizer Status"
              value={allocationResult.optimizer_status || 'Optimal'}
              subtitle="Algorithmic convergence"
              icon={CheckCircleIcon}
              color="emerald"
              badge={allocationResult.optimizer_status}
              badgeType="success"
            />

            <StatCard
              title="Staff Budget"
              value={allocationResult.total_allocated_staff}
              unit="allocated"
              subtitle={`Budget: ${allocationResult.total_staff_budget} personnel`}
              icon={UsersIcon}
              color="indigo"
              badge={allocationResult.budget_conserved ? 'Budget Conserved' : 'Budget Exceeded'}
              badgeType={allocationResult.budget_conserved ? 'success' : 'danger'}
            />

            <StatCard
              title="Current Census"
              value={allocationResult.total_current_staff}
              unit="personnel"
              subtitle={`Target shift: ${allocationResult.shift}`}
              icon={ActivityIcon}
              color="cyan"
              badge={`Shift: ${allocationResult.shift}`}
              badgeType="neutral"
            />

            <StatCard
              title="Objective Score"
              value={allocationResult.objective_score?.toFixed(2) || '0.00'}
              subtitle="Acuity-weighted penalty"
              icon={ShieldCheckIcon}
              color="purple"
              badge="Minimized"
              badgeType="neutral"
            />
          </div>

          {/* Recommendations Table */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-4 shadow-lg backdrop-blur-md">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-bold text-white tracking-wide">
                  Recommended Departmental Staff Allocations
                </h3>
                <p className="text-xs text-slate-400">
                  Optimal headcount ensuring nurse-to-patient ratios, minimum safety limits, and acuity weights
                </p>
              </div>
              <span className="text-xs font-mono text-emerald-400">
                {recommendations.length} Departments Allocated
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="pb-3 font-medium">Department</th>
                    <th className="pb-3 font-medium">Current Staff</th>
                    <th className="pb-3 font-medium">Recommended</th>
                    <th className="pb-3 font-medium">Net Change</th>
                    <th className="pb-3 font-medium">Safety Bounds [Min, Max]</th>
                    <th className="pb-3 font-medium">Rule-Based Baseline</th>
                    <th className="pb-3 font-medium min-w-[200px]">Optimization Rationale</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {recommendations.map((rec) => {
                    const change = rec.net_change
                    const changeColor =
                      change > 0
                        ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
                        : change < 0
                        ? 'text-amber-400 bg-amber-500/10 border-amber-500/30'
                        : 'text-slate-400 bg-slate-800 border-slate-700'

                    return (
                      <tr key={rec.department_code} className="hover:bg-slate-800/40">
                        <td className="py-3 font-semibold text-white">
                          <span className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-emerald-300 font-mono mr-1.5">
                            {rec.department_code}
                          </span>
                          {rec.department_name}
                        </td>
                        <td className="py-3 font-mono text-slate-300">{rec.current_staff}</td>
                        <td className="py-3 font-bold text-white font-mono text-sm">
                          {rec.recommended_staff}
                        </td>
                        <td className="py-3">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold border ${changeColor}`}
                          >
                            {change > 0 ? `+${change}` : change}
                          </span>
                        </td>
                        <td className="py-3 font-mono text-slate-400">
                          [{rec.minimum_staff_constraint}, {rec.maximum_staff_constraint}]
                        </td>
                        <td className="py-3 font-mono text-slate-400">
                          {rec.rule_based_baseline_staff}
                        </td>
                        <td className="py-3 text-[11px] text-slate-300 leading-relaxed">
                          {rec.rationale}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Clinical Governance Notice */}
          {allocationResult.governance_notice && (
            <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4 space-y-2 text-xs text-emerald-200/90 backdrop-blur-md">
              <div className="flex items-center gap-1.5 text-emerald-400 font-semibold text-xs">
                <ShieldCheckIcon className="w-4 h-4" />
                <span>Clinical Governance &amp; Supervisory Approval Notice</span>
              </div>
              <p className="leading-relaxed text-emerald-200/80">
                {allocationResult.governance_notice}
              </p>
            </div>
          )}

          {/* Synthetic Data Disclaimer */}
          <DisclaimerBanner />
        </>
      )}
    </div>
  )
}
