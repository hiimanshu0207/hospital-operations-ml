import { useEffect, useState } from 'react'

function App() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then((res) => res.json())
      .then((data) => {
        setHealth(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 text-white">
      {/* Header */}
      <header className="border-b border-white/10 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-xl font-bold">
              H
            </div>
            <h1 className="text-xl font-semibold tracking-tight">
              Hospital Ops
            </h1>
          </div>
          <span className="text-sm text-slate-400">
            v0.1.0 — Day 1 Setup
          </span>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 via-cyan-300 to-teal-400 bg-clip-text text-transparent">
            Hospital Operations &amp; Workflow Optimization
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            ML-powered decision support for patient demand analysis,
            waiting-time prediction, bed-occupancy monitoring, and
            resource allocation.
          </p>
        </div>

        {/* Backend status card */}
        <div className="max-w-md mx-auto">
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md p-6 shadow-xl">
            <h3 className="text-lg font-semibold mb-4 text-slate-200">
              Backend Connection
            </h3>

            {loading && (
              <div className="flex items-center gap-3 text-slate-400">
                <div className="w-3 h-3 rounded-full bg-yellow-400 animate-pulse" />
                Connecting to API...
              </div>
            )}

            {error && (
              <div className="flex items-center gap-3 text-red-400">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div>
                  <p className="font-medium">Backend offline</p>
                  <p className="text-sm text-slate-500 mt-1">
                    Start the backend with:{' '}
                    <code className="bg-white/10 px-2 py-0.5 rounded text-xs">
                      uvicorn app.main:app --reload
                    </code>
                  </p>
                </div>
              </div>
            )}

            {health && (
              <div className="space-y-3">
                <div className="flex items-center gap-3 text-emerald-400">
                  <div className="w-3 h-3 rounded-full bg-emerald-500" />
                  <span className="font-medium">
                    {health.status}
                  </span>
                </div>
                <div className="text-sm text-slate-400 space-y-1">
                  <p>
                    <span className="text-slate-500">App:</span>{' '}
                    {health.app}
                  </p>
                  <p>
                    <span className="text-slate-500">Version:</span>{' '}
                    {health.version}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-white/10 py-6 text-center text-sm text-slate-500">
        B.Tech CSE Major Project — Built with React, FastAPI &amp; scikit-learn
      </footer>
    </div>
  )
}

export default App
