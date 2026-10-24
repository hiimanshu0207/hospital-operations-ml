import React, { useState, useEffect, useCallback } from 'react'
import Navbar from './components/Navbar'
import Sidebar from './components/Sidebar'
import OverviewTab from './pages/OverviewTab'
import DepartmentsTab from './pages/DepartmentsTab'
import DemandForecastTab from './pages/DemandForecastTab'
import WaitingTimeTab from './pages/WaitingTimeTab'
import SimulationTab from './pages/SimulationTab'
import AllocationTab from './pages/AllocationTab'
import { checkHealth, getHospitalUtilization, getErrorMessage } from './services/api'

export default function App() {
  const [activeTab, setActiveTab] = useState('overview')
  const [backendStatus, setBackendStatus] = useState('connecting') // connected, offline, connecting
  const [lastUpdated, setLastUpdated] = useState(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Global utilization state shared by Overview and Departments tabs
  const [utilizationData, setUtilizationData] = useState(null)
  const [loadingUtilization, setLoadingUtilization] = useState(true)
  const [utilizationError, setUtilizationError] = useState(null)

  const loadData = useCallback(() => {
    setIsRefreshing(true)
    setLoadingUtilization(true)
    setUtilizationError(null)

    checkHealth()
      .then(() => {
        setBackendStatus('connected')
      })
      .catch(() => {
        setBackendStatus('offline')
      })

    getHospitalUtilization()
      .then((data) => {
        setUtilizationData(data)
        setBackendStatus('connected')
        setLastUpdated(new Date().toISOString())
      })
      .catch((err) => {
        const msg = getErrorMessage(err)
        setUtilizationError(msg)
        if (msg.includes('Cannot connect to backend')) {
          setBackendStatus('offline')
        }
      })
      .finally(() => {
        setLoadingUtilization(false)
        setIsRefreshing(false)
      })
  }, [])

  // Initial load on mount
  useEffect(() => {
    let ignore = false

    checkHealth()
      .then(() => {
        if (!ignore) setBackendStatus('connected')
      })
      .catch(() => {
        if (!ignore) setBackendStatus('offline')
      })

    getHospitalUtilization()
      .then((data) => {
        if (!ignore) {
          setUtilizationData(data)
          setBackendStatus('connected')
          setLastUpdated(new Date().toISOString())
        }
      })
      .catch((err) => {
        if (!ignore) {
          const msg = getErrorMessage(err)
          setUtilizationError(msg)
          if (msg.includes('Cannot connect to backend')) {
            setBackendStatus('offline')
          }
        }
      })
      .finally(() => {
        if (!ignore) setLoadingUtilization(false)
      })

    return () => {
      ignore = true
    }
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Background ambient lighting gradients */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl" />
        <div className="absolute top-1/3 -right-40 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 left-1/3 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl" />
      </div>

      {/* Main Top Navigation */}
      <Navbar
        backendStatus={backendStatus}
        lastUpdated={lastUpdated}
        onRefresh={loadData}
        isRefreshing={isRefreshing}
      />

      {/* Main Container */}
      <main className="relative z-10 flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar */}
          <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

          {/* Active Tab Content Area */}
          <section className="flex-1 min-w-0">
            {activeTab === 'overview' && (
              <OverviewTab
                utilizationData={utilizationData}
                loadingUtilization={loadingUtilization}
                utilizationError={utilizationError}
                onRefresh={loadData}
              />
            )}

            {activeTab === 'departments' && (
              <DepartmentsTab
                utilizationData={utilizationData}
                loading={loadingUtilization}
                error={utilizationError}
                onRefresh={loadData}
              />
            )}

            {activeTab === 'forecast' && <DemandForecastTab />}

            {activeTab === 'waiting-time' && <WaitingTimeTab />}

            {activeTab === 'simulation' && <SimulationTab />}

            {activeTab === 'allocation' && <AllocationTab />}
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-slate-900 bg-slate-950/80 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p>
            Major Project &mdash; Hospital Operations &amp; Workflow Optimization using Machine Learning
          </p>
          <p className="font-mono text-[11px] text-slate-600">
            FastAPI &bull; Scikit-Learn &bull; React &bull; Tailwind CSS
          </p>
        </div>
      </footer>
    </div>
  )
}
