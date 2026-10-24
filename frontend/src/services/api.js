/**
 * API service layer for Hospital Operations & Workflow Optimization.
 *
 * Centralizes all HTTP calls to the FastAPI backend.
 * Uses axios for consistent request handling, timeouts, and error formatting.
 */

import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
})

// Error extraction helper
export const getErrorMessage = (error) => {
  if (error.response?.data?.detail) {
    if (typeof error.response.data.detail === 'string') {
      return error.response.data.detail
    }
    if (Array.isArray(error.response.data.detail)) {
      return error.response.data.detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
    }
  }
  if (error.message) {
    if (error.message.includes('Network Error')) {
      return 'Cannot connect to backend server. Ensure FastAPI is running on port 8000.'
    }
    return error.message
  }
  return 'An unexpected error occurred while communicating with the server.'
}

// System Health
export const checkHealth = () => api.get('/health').then((res) => res.data)

// Hospital & Department Metrics
export const getDepartments = () => api.get('/api/v1/departments').then((res) => res.data)
export const getDepartmentMetrics = (id) => api.get(`/api/v1/departments/${id}/metrics`).then((res) => res.data)

// Beds
export const getBedsSummary = () => api.get('/api/v1/beds/summary').then((res) => res.data)
export const getBeds = () => api.get('/api/v1/beds').then((res) => res.data)

// Patient Visits
export const getVisitsSummary = () => api.get('/api/v1/patient-visits/summary').then((res) => res.data)
export const getRecentVisits = (limit = 10) =>
  api.get(`/api/v1/patient-visits/recent?limit=${limit}`).then((res) => res.data)

// Machine Learning Predictions
export const predictDemand = ({ department_code, horizon_hours = 24, start_time = null }) =>
  api
    .post('/api/v1/predictions/demand', {
      department_code,
      horizon_hours: Number(horizon_hours),
      start_time,
    })
    .then((res) => res.data)

export const predictWaitingTime = ({
  department_code,
  acuity_level,
  queue_length = 0,
  staff_available = 4,
  patient_age_group = '36-50',
}) =>
  api
    .post('/api/v1/predictions/waiting-time', {
      department_code,
      acuity_level: Number(acuity_level),
      queue_length: Number(queue_length),
      staff_available: Number(staff_available),
      patient_age_group,
    })
    .then((res) => res.data)

// Resource Utilization & Optimization
export const getHospitalUtilization = () =>
  api.get('/api/v1/optimization/utilization').then((res) => res.data)

export const simulateScenario = ({
  arrival_surge_pct = 0.0,
  staff_adjustments = {},
  bed_capacity_adjustments = {},
  time_horizon_hours = 12,
  simulation_seed = 42,
}) =>
  api
    .post('/api/v1/optimization/simulate', {
      arrival_surge_pct: Number(arrival_surge_pct),
      staff_adjustments,
      bed_capacity_adjustments,
      time_horizon_hours: Number(time_horizon_hours),
      simulation_seed: Number(simulation_seed),
    })
    .then((res) => res.data)

export const optimizeStaffAllocation = ({
  shift = 'All',
  total_staff_budget = null,
  min_staff_per_dept = null,
  max_staff_per_dept = null,
  priority_weights = null,
}) =>
  api
    .post('/api/v1/optimization/allocate', {
      shift,
      total_staff_budget: total_staff_budget !== null && total_staff_budget !== '' ? Number(total_staff_budget) : null,
      min_staff_per_dept,
      max_staff_per_dept,
      priority_weights,
    })
    .then((res) => res.data)

export default api
