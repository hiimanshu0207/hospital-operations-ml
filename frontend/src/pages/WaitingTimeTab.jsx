import React, { useState, useEffect } from 'react'
import DisclaimerBanner from '../components/DisclaimerBanner'
import LoadingSpinner from '../components/LoadingSkeleton'
import ErrorAlert from '../components/ErrorAlert'
import {
  ClockIcon,
  SparklesIcon,
  InfoIcon,
} from '../components/Icons'
import { predictWaitingTime, getErrorMessage } from '../services/api'

const DEPARTMENTS = [
  { code: 'ED', name: 'Emergency Department' },
  { code: 'ICU', name: 'Intensive Care Unit' },
  { code: 'GEN', name: 'General Inpatient Ward' },
  { code: 'SURG', name: 'Surgical Services' },
  { code: 'PED', name: 'Pediatrics Department' },
]

const ACUITY_LEVELS = [
  { level: 1, label: 'ESI 1: Resuscitation', desc: 'Immediate life threat', color: 'border-rose-500/40 text-rose-300 bg-rose-500/10' },
  { level: 2, label: 'ESI 2: Emergent', desc: 'High risk / severe distress', color: 'border-orange-500/40 text-orange-300 bg-orange-500/10' },
  { level: 3, label: 'ESI 3: Urgent', desc: 'Multiple clinical resources', color: 'border-amber-500/40 text-amber-300 bg-amber-500/10' },
  { level: 4, label: 'ESI 4: Less Urgent', desc: 'Single clinical resource', color: 'border-blue-500/40 text-blue-300 bg-blue-500/10' },
  { level: 5, label: 'ESI 5: Non-urgent', desc: 'Minimal intervention needed', color: 'border-emerald-500/40 text-emerald-300 bg-emerald-500/10' },
]

const AGE_GROUPS = ['0-17', '18-35', '36-50', '51-65', '65+']

export default function WaitingTimeTab() {
  const [departmentCode, setDepartmentCode] = useState('ED')
  const [acuityLevel, setAcuityLevel] = useState(3)
  const [queueLength, setQueueLength] = useState(5)
  const [staffAvailable, setStaffAvailable] = useState(4)
  const [ageGroup, setAgeGroup] = useState('36-50')

  const [prediction, setPrediction] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const handleSubmit = (e) => {
    if (e) e.preventDefault()
    setLoading(true)
    setError(null)

    predictWaitingTime({
      department_code: departmentCode,
      acuity_level: acuityLevel,
      queue_length: queueLength,
      staff_available: staffAvailable,
      patient_age_group: ageGroup,
    })
      .then((data) => {
        setPrediction(data)
      })
      .catch((err) => {
        setError(getErrorMessage(err))
      })
      .finally(() => {
        setLoading(false)
      })
  }

  // Pre-load an initial prediction on mount
  useEffect(() => {
    let ignore = false
    predictWaitingTime({
      department_code: 'ED',
      acuity_level: 3,
      queue_length: 5,
      staff_available: 4,
      patient_age_group: '36-50',
    })
      .then((data) => {
        if (!ignore) setPrediction(data)
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-bold text-white tracking-tight">
          Patient Waiting-Time Prediction
        </h2>
        <p className="text-xs text-slate-400">
          Leakage-free regression inference estimating minutes to physician triage based on queue depth, staffing ratios, and clinical acuity
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Form Controls Column (5 cols) */}
        <div className="lg:col-span-5 rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-4 shadow-lg backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h3 className="text-sm font-semibold text-white">Triage &amp; Queue Parameters</h3>
            <span className="text-[11px] font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
              Live Input
            </span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Department */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Clinical Department</label>
              <select
                value={departmentCode}
                onChange={(e) => setDepartmentCode(e.target.value)}
                className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
              >
                {DEPARTMENTS.map((dept) => (
                  <option key={dept.code} value={dept.code}>
                    {dept.code} — {dept.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Acuity Level */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">
                Triage Acuity Level (ESI)
              </label>
              <div className="space-y-1.5">
                {ACUITY_LEVELS.map((item) => (
                  <button
                    key={item.level}
                    type="button"
                    onClick={() => setAcuityLevel(item.level)}
                    className={`w-full text-left px-3 py-2 rounded-xl text-xs transition-all border flex items-center justify-between ${
                      acuityLevel === item.level
                        ? `${item.color} font-semibold ring-1 ring-white/20 shadow-sm`
                        : 'bg-slate-950/60 border-slate-800/80 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <div>
                      <p className="font-medium">{item.label}</p>
                      <p className="text-[10px] text-slate-500">{item.desc}</p>
                    </div>
                    {acuityLevel === item.level && (
                      <span className="w-2 h-2 rounded-full bg-cyan-400" />
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Queue Length Slider */}
            <div className="space-y-1.5 pt-1">
              <div className="flex justify-between items-center text-xs">
                <span className="font-medium text-slate-300">Patients in Queue at Arrival</span>
                <span className="font-mono text-cyan-400 font-bold">{queueLength} patients</span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                value={queueLength}
                onChange={(e) => setQueueLength(Number(e.target.value))}
                className="w-full accent-cyan-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>0 (Empty)</span>
                <span>15</span>
                <span>30 (Overcrowded)</span>
              </div>
            </div>

            {/* Available Staff Slider */}
            <div className="space-y-1.5 pt-1">
              <div className="flex justify-between items-center text-xs">
                <span className="font-medium text-slate-300">Active Staff Available</span>
                <span className="font-mono text-indigo-400 font-bold">{staffAvailable} personnel</span>
              </div>
              <input
                type="range"
                min="1"
                max="15"
                value={staffAvailable}
                onChange={(e) => setStaffAvailable(Number(e.target.value))}
                className="w-full accent-indigo-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>1 (Skeleton)</span>
                <span>8</span>
                <span>15 (Max)</span>
              </div>
            </div>

            {/* Age Group */}
            <div className="space-y-1.5 pt-1">
              <label className="text-xs font-medium text-slate-300">Patient Age Demographic</label>
              <div className="grid grid-cols-5 gap-1.5">
                {AGE_GROUPS.map((grp) => (
                  <button
                    key={grp}
                    type="button"
                    onClick={() => setAgeGroup(grp)}
                    className={`py-1.5 text-center rounded-lg text-xs font-medium transition-all border ${
                      ageGroup === grp
                        ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 font-bold'
                        : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    {grp}
                  </button>
                ))}
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-3 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-semibold text-xs tracking-wide shadow-md shadow-cyan-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <SparklesIcon className="w-4 h-4" />
              {loading ? 'Evaluating Model...' : 'Calculate Predicted Wait Time'}
            </button>
          </form>
        </div>

        {/* Prediction Output Column (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {error && (
            <ErrorAlert
              title="Prediction request failed"
              message={error}
              onRetry={handleSubmit}
            />
          )}

          {loading && !prediction && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-12 text-center backdrop-blur-md">
              <LoadingSpinner text="Computing regression inference with uncertainty intervals..." />
            </div>
          )}

          {prediction && (
            <div className="space-y-4">
              {/* Main Result Card */}
              <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-cyan-500/15 via-slate-900/90 to-slate-900/90 p-6 border border-cyan-500/30 backdrop-blur-md shadow-xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                      <ClockIcon className="w-3.5 h-3.5" />
                      Predicted Triage Waiting Time
                    </span>
                    <div className="flex items-baseline gap-2">
                      <span className="text-4xl md:text-5xl font-extrabold text-white tracking-tight">
                        {prediction.estimated_waiting_time_minutes?.toFixed(1)}
                      </span>
                      <span className="text-lg font-semibold text-slate-400">minutes</span>
                    </div>
                  </div>

                  {/* 95% Confidence Bounds Badge */}
                  <div className="sm:text-right space-y-1">
                    <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider">
                      95% Confidence Interval
                    </span>
                    <div className="inline-block px-3 py-1.5 rounded-xl bg-slate-950/80 border border-slate-700/80 font-mono text-xs text-cyan-300 font-semibold shadow-inner">
                      [{prediction.confidence_lower?.toFixed(1)}m — {prediction.confidence_upper?.toFixed(1)}m]
                    </div>
                  </div>
                </div>

                {/* Model & Operational Context */}
                <div className="mt-6 pt-4 border-t border-slate-800/80 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div>
                    <span className="text-slate-500 block text-[10px]">Department</span>
                    <span className="font-semibold text-slate-200">
                      {prediction.department_name} ({prediction.department_code})
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Acuity ESI</span>
                    <span className="font-semibold text-amber-300">Level {prediction.acuity_level}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Model Artifact</span>
                    <span className="font-semibold text-slate-200 font-mono truncate block">
                      {prediction.model_name}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Queue/Staff Ratio</span>
                    <span className="font-semibold text-cyan-400 font-mono">
                      {(queueLength / Math.max(1, staffAvailable)).toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Clinical Workflow Interpretation */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 space-y-2 text-xs text-slate-300 backdrop-blur-md">
                <div className="flex items-center gap-1.5 text-cyan-400 font-semibold text-xs">
                  <InfoIcon className="w-4 h-4" />
                  <span>Clinical Decision Support Context</span>
                </div>
                <p className="leading-relaxed text-slate-400">
                  Patients assigned to <strong>ESI {prediction.acuity_level}</strong> in{' '}
                  <strong>{prediction.department_name}</strong> facing an arrival queue of{' '}
                  <strong>{queueLength}</strong> with <strong>{staffAvailable}</strong> staff members on duty
                  are statistically projected to wait approximately{' '}
                  <strong className="text-white">
                    {prediction.estimated_waiting_time_minutes?.toFixed(1)} minutes
                  </strong>{' '}
                  before clinical service commences.
                </p>
              </div>

              {/* Synthetic Data Disclaimer */}
              <DisclaimerBanner text={prediction.disclaimer} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
