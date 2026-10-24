import React, { useState, useEffect } from 'react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'
import DisclaimerBanner from '../components/DisclaimerBanner'
import { ChartSkeleton } from '../components/LoadingSkeleton'
import ErrorAlert from '../components/ErrorAlert'
import StatCard from '../components/StatCard'
import {
  TrendingUpIcon,
  ClockIcon,
  ActivityIcon,
  ShieldCheckIcon,
} from '../components/Icons'
import { predictDemand, getErrorMessage } from '../services/api'

const DEPARTMENTS = [
  { code: 'ED', name: 'Emergency Department' },
  { code: 'ICU', name: 'Intensive Care Unit' },
  { code: 'GEN', name: 'General Inpatient Ward' },
  { code: 'SURG', name: 'Surgical Services' },
  { code: 'PED', name: 'Pediatrics Department' },
]

const HORIZONS = [12, 24, 48, 72]

export default function DemandForecastTab() {
  const [selectedDept, setSelectedDept] = useState('ED')
  const [horizon, setHorizon] = useState(24)
  const [forecastData, setForecastData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchForecast = (deptCode, horizonHours) => {
    setLoading(true)
    setError(null)

    predictDemand({ department_code: deptCode, horizon_hours: horizonHours })
      .then((data) => {
        setForecastData(data)
      })
      .catch((err) => {
        setError(getErrorMessage(err))
      })
      .finally(() => {
        setLoading(false)
      })
  }

  // Load initial forecast on mount
  useEffect(() => {
    let ignore = false
    predictDemand({ department_code: 'ED', horizon_hours: 24 })
      .then((data) => {
        if (!ignore) setForecastData(data)
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

  const handleDeptChange = (deptCode) => {
    setSelectedDept(deptCode)
    fetchForecast(deptCode, horizon)
  }

  const handleHorizonChange = (h) => {
    setHorizon(h)
    fetchForecast(selectedDept, h)
  }

  // Prepare chart data with formatted labels
  const chartData =
    forecastData?.hourly_forecasts?.map((item) => {
      const date = new Date(item.timestamp)
      const timeLabel = isNaN(date.getTime())
        ? `+${item.hour}h`
        : date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

      return {
        ...item,
        timeLabel,
        predicted: Number(item.predicted_arrivals.toFixed(1)),
        lower: Number(item.confidence_lower.toFixed(1)),
        upper: Number(item.confidence_upper.toFixed(1)),
      }
    }) || []

  // Compute peak hour
  const peakHourItem =
    chartData.length > 0
      ? chartData.reduce((prev, curr) => (curr.predicted > prev.predicted ? curr : prev), chartData[0])
      : null

  const avgArrivals =
    forecastData?.total_predicted_arrivals && forecastData.horizon_hours
      ? (forecastData.total_predicted_arrivals / forecastData.horizon_hours).toFixed(1)
      : '0.0'

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-4 shadow-lg backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">
              Patient Demand Forecasting
            </h2>
            <p className="text-xs text-slate-400">
              Machine learning arrival projections based on calendar dynamics, historical surges, and weather features
            </p>
          </div>

          <button
            type="button"
            onClick={() => fetchForecast(selectedDept, horizon)}
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold shadow-md shadow-cyan-500/20 transition-all disabled:opacity-50"
          >
            <TrendingUpIcon className="w-4 h-4" />
            {loading ? 'Forecasting...' : 'Update Trajectory'}
          </button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 pt-3 border-t border-slate-800/80">
          {/* Department Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Department:</span>
            <div className="flex flex-wrap gap-1.5">
              {DEPARTMENTS.map((dept) => (
                <button
                  key={dept.code}
                  type="button"
                  onClick={() => handleDeptChange(dept.code)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    selectedDept === dept.code
                      ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
                      : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  {dept.code} — {dept.name}
                </button>
              ))}
            </div>
          </div>

          {/* Horizon Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Horizon:</span>
            <div className="flex gap-1.5">
              {HORIZONS.map((h) => (
                <button
                  key={h}
                  type="button"
                  onClick={() => handleHorizonChange(h)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    horizon === h
                      ? 'bg-indigo-500 text-white font-bold shadow-md shadow-indigo-500/20'
                      : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  {h} Hours
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {error && (
        <ErrorAlert
          title="Demand forecast request failed"
          message={error}
          onRetry={() => fetchForecast(selectedDept, horizon)}
        />
      )}

      {loading && !forecastData && <ChartSkeleton />}

      {forecastData && (
        <>
          {/* Summary KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Total Predicted Inflow"
              value={forecastData.total_predicted_arrivals?.toFixed(1) || 0}
              unit="patients"
              subtitle={`Over ${forecastData.horizon_hours} hours horizon`}
              icon={TrendingUpIcon}
              color="cyan"
              badge={selectedDept}
              badgeType="neutral"
            />

            <StatCard
              title="Average Arrival Rate"
              value={avgArrivals}
              unit="pts/hr"
              subtitle="Projected flow density"
              icon={ClockIcon}
              color="indigo"
              badge="Trajectory"
              badgeType="neutral"
            />

            <StatCard
              title="Peak Forecast Hour"
              value={peakHourItem ? `${peakHourItem.predicted}` : '—'}
              unit={peakHourItem ? 'pts' : ''}
              subtitle={peakHourItem ? `At hour ${peakHourItem.timeLabel}` : 'N/A'}
              icon={ActivityIcon}
              color="amber"
              badge="Max Volume"
              badgeType="warning"
            />

            <StatCard
              title="Forecasting Engine"
              value={forecastData.model_name || 'ML Model'}
              subtitle={`Version ${forecastData.model_version || '1.0'}`}
              icon={ShieldCheckIcon}
              color="purple"
              badge="Active Artifact"
              badgeType="success"
            />
          </div>

          {/* Forecast Chart */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-4 shadow-lg backdrop-blur-md">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-bold text-white tracking-wide">
                  Projected Patient Inflow &amp; 95% Confidence Bounds
                </h3>
                <p className="text-xs text-slate-400">
                  Hourly expected arrivals with upper and lower uncertainty intervals
                </p>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="flex items-center gap-1.5 text-cyan-400 font-medium">
                  <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" /> Expected Arrivals
                </span>
                <span className="flex items-center gap-1.5 text-cyan-500/50 font-medium">
                  <span className="w-2.5 h-2.5 rounded-full bg-cyan-500/30" /> 95% Confidence Band
                </span>
              </div>
            </div>

            <div className="h-72 w-full pt-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={chartData}
                  margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="colorArrivals" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="colorBand" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="timeLabel"
                    stroke="#64748b"
                    fontSize={11}
                    tickLine={false}
                  />
                  <YAxis
                    stroke="#64748b"
                    fontSize={11}
                    tickLine={false}
                    domain={['auto', 'auto']}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '0.75rem',
                      color: '#f8fafc',
                      fontSize: '12px',
                    }}
                    formatter={(val, name) => [
                      `${val} arrivals`,
                      name === 'predicted' ? 'Expected' : name === 'upper' ? 'Upper Bound' : 'Lower Bound',
                    ]}
                    labelFormatter={(label) => `Timestamp: ${label}`}
                  />
                  {/* Confidence Band */}
                  <Area
                    type="monotone"
                    dataKey="upper"
                    stroke="#38bdf8"
                    strokeDasharray="2 2"
                    strokeWidth={1}
                    fillOpacity={1}
                    fill="url(#colorBand)"
                  />
                  {/* Predicted Arrivals Line & Gradient */}
                  <Area
                    type="monotone"
                    dataKey="predicted"
                    stroke="#06b6d4"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#colorArrivals)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Hourly Breakdown Table */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-4 shadow-lg backdrop-blur-md">
            <h3 className="text-sm font-bold text-white tracking-wide">
              Hourly Forecast Telemetry ({chartData.length} Intervals)
            </h3>
            <div className="overflow-x-auto max-h-60 overflow-y-auto scrollbar-thin">
              <table className="w-full text-left text-xs">
                <thead className="sticky top-0 bg-slate-900/90 backdrop-blur-sm z-10">
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="pb-2 font-medium">Hour Ahead</th>
                    <th className="pb-2 font-medium">Timestamp</th>
                    <th className="pb-2 font-medium">Predicted Inflow</th>
                    <th className="pb-2 font-medium">Lower 95% Bound</th>
                    <th className="pb-2 font-medium">Upper 95% Bound</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {chartData.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40">
                      <td className="py-2 font-mono text-cyan-400 font-medium">+{item.hour}h</td>
                      <td className="py-2 text-slate-400 font-mono">{item.timeLabel}</td>
                      <td className="py-2 font-semibold text-white">{item.predicted} pts</td>
                      <td className="py-2 text-slate-400">{item.lower} pts</td>
                      <td className="py-2 text-slate-400">{item.upper} pts</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Synthetic Data Disclaimer */}
          <DisclaimerBanner text={forecastData.disclaimer} />
        </>
      )}
    </div>
  )
}
