import React, { useState, useEffect } from 'react'
import DisclaimerBanner from '../components/DisclaimerBanner'
import LoadingSpinner from '../components/LoadingSkeleton'
import ErrorAlert from '../components/ErrorAlert'
import StatCard from '../components/StatCard'
import {
  SlidersIcon,
  ActivityIcon,
  ClockIcon,
  AlertTriangleIcon,
  SparklesIcon,
  BedIcon,
  UsersIcon,
  InfoIcon,
} from '../components/Icons'
import { simulateScenario, getErrorMessage } from '../services/api'

const DEPARTMENTS = ['ED', 'ICU', 'GEN', 'SURG', 'PED']

export default function SimulationTab() {
  const [arrivalSurgePct, setArrivalSurgePct] = useState(20)
  const [horizonHours, setHorizonHours] = useState(12)
  const [staffAdjustments, setStaffAdjustments] = useState({ ED: 2, ICU: 0, GEN: -1, SURG: 0, PED: 0 })
  const [bedAdjustments, setBedAdjustments] = useState({ ED: 0, ICU: 0, GEN: 0, SURG: 0, PED: 0 })

  const [simulationResult, setSimulationResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const handleRunSimulation = (e) => {
    if (e) e.preventDefault()
    setLoading(true)
    setError(null)

    // Filter out 0 adjustments to keep payload clean
    const cleanStaff = Object.fromEntries(
      Object.entries(staffAdjustments).filter(([, val]) => val !== 0)
    )
    const cleanBeds = Object.fromEntries(
      Object.entries(bedAdjustments).filter(([, val]) => val !== 0)
    )

    simulateScenario({
      arrival_surge_pct: Number(arrivalSurgePct),
      staff_adjustments: cleanStaff,
      bed_capacity_adjustments: cleanBeds,
      time_horizon_hours: Number(horizonHours),
      simulation_seed: 42,
    })
      .then((data) => {
        setSimulationResult(data)
      })
      .catch((err) => {
        setError(getErrorMessage(err))
      })
      .finally(() => {
        setLoading(false)
      })
  }

  // Run baseline simulation on mount
  useEffect(() => {
    let ignore = false
    simulateScenario({
      arrival_surge_pct: 20,
      staff_adjustments: { ED: 2, GEN: -1 },
      bed_capacity_adjustments: {},
      time_horizon_hours: 12,
      simulation_seed: 42,
    })
      .then((data) => {
        if (!ignore) setSimulationResult(data)
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

  const updateStaff = (dept, delta) => {
    setStaffAdjustments((prev) => ({
      ...prev,
      [dept]: Math.max(-5, Math.min(10, (prev[dept] || 0) + delta)),
    }))
  }

  const updateBed = (dept, delta) => {
    setBedAdjustments((prev) => ({
      ...prev,
      [dept]: Math.max(-10, Math.min(20, (prev[dept] || 0) + delta)),
    }))
  }

  const impact = simulationResult?.overall_impact

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-bold text-white tracking-tight">
          Hospital What-If Scenario Simulation
        </h2>
        <p className="text-xs text-slate-400">
          Stress-test clinical capacity under patient arrival surges, staffing shifts, and physical bed expansions
        </p>
      </div>

      {/* Simulator Controls Card */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-5 shadow-lg backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2">
            <SlidersIcon className="w-4 h-4 text-rose-400" />
            <h3 className="text-sm font-semibold text-white">Simulation Scenario Controls</h3>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">
            Stochastic Queue &amp; Bed Engine
          </span>
        </div>

        {/* Global Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Patient Arrival Surge */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-medium text-slate-300">Patient Arrival Surge / Drop</span>
              <span
                className={`font-mono font-bold text-sm ${
                  arrivalSurgePct > 0
                    ? 'text-rose-400'
                    : arrivalSurgePct < 0
                    ? 'text-emerald-400'
                    : 'text-slate-300'
                }`}
              >
                {arrivalSurgePct > 0 ? `+${arrivalSurgePct}%` : `${arrivalSurgePct}%`}
              </span>
            </div>
            <input
              type="range"
              min="-50"
              max="100"
              step="5"
              value={arrivalSurgePct}
              onChange={(e) => setArrivalSurgePct(Number(e.target.value))}
              className="w-full accent-rose-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />
            {/* Quick buttons */}
            <div className="flex gap-1.5 pt-1">
              {[-25, 0, 20, 50, 100].map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => setArrivalSurgePct(val)}
                  className={`px-2 py-1 rounded text-[10px] font-mono transition-all border ${
                    arrivalSurgePct === val
                      ? 'bg-rose-500 text-white font-bold border-rose-400 shadow'
                      : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white'
                  }`}
                >
                  {val > 0 ? `+${val}%` : `${val}%`}
                </button>
              ))}
            </div>
          </div>

          {/* Time Horizon */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-medium text-slate-300">Simulation Horizon Window</span>
              <span className="font-mono text-cyan-400 font-bold">{horizonHours} Hours</span>
            </div>
            <div className="grid grid-cols-4 gap-2 pt-1">
              {[6, 12, 24, 48].map((h) => (
                <button
                  key={h}
                  type="button"
                  onClick={() => setHorizonHours(h)}
                  className={`py-2 rounded-xl text-xs font-semibold transition-all border ${
                    horizonHours === h
                      ? 'bg-cyan-500 text-slate-950 border-cyan-400 shadow'
                      : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white'
                  }`}
                >
                  {h} Hours
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Department Fine-Tuning Steppers */}
        <div className="space-y-3 pt-3 border-t border-slate-800/80">
          <div className="flex justify-between items-center text-xs">
            <span className="font-semibold text-slate-200">
              Department Resource Adjustments (Relative Shifts)
            </span>
            <span className="text-[11px] text-slate-500">Staff (± personnel) / Beds (± capacity)</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {DEPARTMENTS.map((dept) => {
              const staffVal = staffAdjustments[dept] || 0
              const bedVal = bedAdjustments[dept] || 0

              return (
                <div
                  key={dept}
                  className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2.5"
                >
                  <span className="text-xs font-bold text-white block pb-1 border-b border-slate-800">
                    {dept}
                  </span>

                  {/* Staff Adjuster */}
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400 text-[11px] flex items-center gap-1">
                      <UsersIcon className="w-3 h-3 text-indigo-400" /> Staff:
                    </span>
                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => updateStaff(dept, -1)}
                        className="w-5 h-5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold flex items-center justify-center text-xs"
                      >
                        -
                      </button>
                      <span
                        className={`w-6 text-center font-mono text-xs font-bold ${
                          staffVal > 0 ? 'text-emerald-400' : staffVal < 0 ? 'text-rose-400' : 'text-slate-400'
                        }`}
                      >
                        {staffVal > 0 ? `+${staffVal}` : staffVal}
                      </span>
                      <button
                        type="button"
                        onClick={() => updateStaff(dept, 1)}
                        className="w-5 h-5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold flex items-center justify-center text-xs"
                      >
                        +
                      </button>
                    </div>
                  </div>

                  {/* Bed Adjuster */}
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400 text-[11px] flex items-center gap-1">
                      <BedIcon className="w-3 h-3 text-cyan-400" /> Beds:
                    </span>
                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => updateBed(dept, -1)}
                        className="w-5 h-5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold flex items-center justify-center text-xs"
                      >
                        -
                      </button>
                      <span
                        className={`w-6 text-center font-mono text-xs font-bold ${
                          bedVal > 0 ? 'text-emerald-400' : bedVal < 0 ? 'text-rose-400' : 'text-slate-400'
                        }`}
                      >
                        {bedVal > 0 ? `+${bedVal}` : bedVal}
                      </span>
                      <button
                        type="button"
                        onClick={() => updateBed(dept, 1)}
                        className="w-5 h-5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold flex items-center justify-center text-xs"
                      >
                        +
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Action Button */}
        <button
          type="button"
          onClick={handleRunSimulation}
          disabled={loading}
          className="w-full py-2.5 rounded-xl bg-gradient-to-r from-rose-600 via-pink-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 text-white font-semibold text-xs tracking-wide shadow-md shadow-rose-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <SparklesIcon className="w-4 h-4" />
          {loading ? 'Simulating Operational Shift...' : 'Run What-If Simulation'}
        </button>
      </div>

      {error && (
        <ErrorAlert
          title="Simulation failed"
          message={error}
          onRetry={handleRunSimulation}
        />
      )}

      {loading && !simulationResult && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-12 text-center backdrop-blur-md">
          <LoadingSpinner text="Simulating stochastic patient arrivals and bed transitions..." />
        </div>
      )}

      {simulationResult && (
        <>
          {/* Overall Impact Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Baseline Avg Wait"
              value={`${impact?.average_baseline_wait_minutes?.toFixed(1) || 0}`}
              unit="min"
              subtitle="Current operational state"
              icon={ClockIcon}
              color="indigo"
              badge="Baseline"
              badgeType="neutral"
            />

            <StatCard
              title="Simulated Avg Wait"
              value={`${impact?.average_simulated_wait_minutes?.toFixed(1) || 0}`}
              unit="min"
              subtitle="Under simulated parameters"
              icon={ClockIcon}
              color={impact?.net_wait_time_delta_minutes > 0 ? 'rose' : 'emerald'}
              badge={
                impact?.net_wait_time_delta_minutes > 0
                  ? `+${impact?.net_wait_time_delta_minutes.toFixed(1)}m delay`
                  : `${impact?.net_wait_time_delta_minutes.toFixed(1)}m reduction`
              }
              badgeType={impact?.net_wait_time_delta_minutes > 0 ? 'danger' : 'success'}
            />

            <StatCard
              title="Surge Severity"
              value={impact?.surge_severity || 'Nominal'}
              subtitle={`Inflow adjustment: ${arrivalSurgePct > 0 ? `+${arrivalSurgePct}%` : `${arrivalSurgePct}%`}`}
              icon={ActivityIcon}
              color={impact?.surge_severity === 'Severe Surge' ? 'rose' : 'amber'}
              badge={impact?.surge_severity || 'Nominal'}
              badgeType={
                impact?.surge_severity === 'Severe Surge'
                  ? 'danger'
                  : impact?.surge_severity === 'Moderate Surge'
                  ? 'warning'
                  : 'success'
              }
            />

            <StatCard
              title="Horizon Window"
              value={simulationResult.simulation_parameters?.time_horizon_hours || 12}
              unit="hours"
              subtitle="Stochastic forward window"
              icon={SlidersIcon}
              color="cyan"
              badge="Seed: 42"
              badgeType="neutral"
            />
          </div>

          {/* Department Baseline vs Simulated Comparison Table */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-4 shadow-lg backdrop-blur-md">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white tracking-wide">
                  Departmental Operational Impact (Baseline vs Simulated)
                </h3>
                <p className="text-xs text-slate-400">
                  Detailed shift analysis in bed occupancy, queue depth, and triage wait minutes
                </p>
              </div>
              <span className="text-xs font-mono text-rose-400">
                {simulationResult.department_comparisons?.length} Departments Modeled
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="pb-3 font-medium">Department</th>
                    <th className="pb-3 font-medium">Staff (Base → Sim)</th>
                    <th className="pb-3 font-medium">Beds (Base → Sim)</th>
                    <th className="pb-3 font-medium">Bed Util. (Δ)</th>
                    <th className="pb-3 font-medium">Queue (Δ)</th>
                    <th className="pb-3 font-medium">Wait Time (Base → Sim)</th>
                    <th className="pb-3 font-medium">Projected Alerts</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {simulationResult.department_comparisons?.map((comp) => {
                    const delta = comp.delta
                    const waitDelta = delta.wait_time_delta_minutes || 0

                    return (
                      <tr key={comp.department_code} className="hover:bg-slate-800/40">
                        <td className="py-3 font-semibold text-white">
                          <span className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-cyan-300 font-mono mr-1.5">
                            {comp.department_code}
                          </span>
                          {comp.department_name}
                        </td>
                        <td className="py-3">
                          <span className="text-slate-400">{comp.baseline.active_staff}</span>
                          <span className="mx-1 text-slate-500">→</span>
                          <span className="font-semibold text-white">{comp.simulated.active_staff}</span>
                          {delta.staff_change !== 0 && (
                            <span
                              className={`ml-1.5 text-[10px] font-mono ${
                                delta.staff_change > 0 ? 'text-emerald-400' : 'text-rose-400'
                              }`}
                            >
                              ({delta.staff_change > 0 ? `+${delta.staff_change}` : delta.staff_change})
                            </span>
                          )}
                        </td>
                        <td className="py-3">
                          <span className="text-slate-400">
                            {comp.baseline.occupied_beds}/{comp.baseline.total_beds}
                          </span>
                          <span className="mx-1 text-slate-500">→</span>
                          <span className="font-semibold text-white">
                            {comp.simulated.occupied_beds}/{comp.simulated.total_beds}
                          </span>
                        </td>
                        <td className="py-3">
                          <span className="font-mono text-white">
                            {comp.simulated.bed_utilization_pct?.toFixed(1)}%
                          </span>
                          <span
                            className={`ml-1 text-[10px] font-mono ${
                              delta.bed_utilization_delta_pct > 0
                                ? 'text-rose-400'
                                : delta.bed_utilization_delta_pct < 0
                                ? 'text-emerald-400'
                                : 'text-slate-500'
                            }`}
                          >
                            ({delta.bed_utilization_delta_pct > 0 ? '+' : ''}
                            {delta.bed_utilization_delta_pct?.toFixed(1)}%)
                          </span>
                        </td>
                        <td className="py-3">
                          <span className="font-mono text-white">{comp.simulated.queue_length}</span>
                          <span
                            className={`ml-1 text-[10px] font-mono ${
                              delta.queue_length_delta > 0
                                ? 'text-rose-400'
                                : delta.queue_length_delta < 0
                                ? 'text-emerald-400'
                                : 'text-slate-500'
                            }`}
                          >
                            ({delta.queue_length_delta > 0 ? '+' : ''}
                            {delta.queue_length_delta})
                          </span>
                        </td>
                        <td className="py-3">
                          <span className="text-slate-400">
                            {comp.baseline.estimated_wait_time_minutes?.toFixed(1)}m
                          </span>
                          <span className="mx-1 text-slate-500">→</span>
                          <span className="font-semibold text-amber-300">
                            {comp.simulated.estimated_wait_time_minutes?.toFixed(1)}m
                          </span>
                          <span
                            className={`ml-1.5 text-[10px] font-mono font-bold ${
                              waitDelta > 0 ? 'text-rose-400' : waitDelta < 0 ? 'text-emerald-400' : 'text-slate-500'
                            }`}
                          >
                            ({waitDelta > 0 ? `+${waitDelta.toFixed(1)}m` : `${waitDelta.toFixed(1)}m`})
                          </span>
                        </td>
                        <td className="py-3">
                          {comp.projected_warnings && comp.projected_warnings.length > 0 ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                              <AlertTriangleIcon className="w-3 h-3" />
                              {comp.projected_warnings.length} warning(s)
                            </span>
                          ) : (
                            <span className="text-[11px] text-emerald-400 font-medium">Nominal</span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Assumptions List */}
          {simulationResult.assumptions && simulationResult.assumptions.length > 0 && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 space-y-2 text-xs text-slate-300 backdrop-blur-md">
              <div className="flex items-center gap-1.5 text-cyan-400 font-semibold text-xs">
                <InfoIcon className="w-4 h-4" />
                <span>Simulation Model Assumptions</span>
              </div>
              <ul className="space-y-1 pl-4 list-disc text-slate-400 text-[11px]">
                {simulationResult.assumptions.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Synthetic Data Disclaimer */}
          <DisclaimerBanner text={simulationResult.disclaimer} />
        </>
      )}
    </div>
  )
}
