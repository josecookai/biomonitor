const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || ''

export interface WeekStats {
  week_start: string
  crossfit_sessions: number
  walking_distance_km: number
  walking_time_min: number
  total_activities: number
}

export interface WeeklyStatEntry {
  week: string
  crossfit_sessions: number
  walking_distance_km: number
  walking_time_min: number
  total_activities: number
}

export interface ActivityItem {
  id: number
  name: string
  type: string
  start_date: string
  distance: number | null
  moving_time: number
  average_heartrate: number | null
  max_heartrate: number | null
  is_crossfit: boolean
  is_walking: boolean
  calories?: number
}

export interface DailyDataPoint {
  date: string
  crossfit: number
  walking: number
}

export interface ShareCardData {
  week: string
  crossfit: { completed: number; target: number }
  walking: { distance_km: number }
  hrv: number | null
  resting_hr: number | null
}

export interface HealthMetric {
  date: string
  metric_type: string
  value: number
  unit: string
}

export interface LatestHealthMetrics {
  resting_hr?: number
  hrv?: number
  sleep_hours?: number
  steps?: number
  source: string
}

export interface CrossFitWorkout {
  id: number
  wod_name: string
  date: string
  time: string | null
  rounds: number | null
  reps: number | null
  weight: number | null
  rpe: number | null
  notes: string | null
}

export interface CrossFitWorkoutInput {
  wod_name: string
  date: string
  time?: string
  rounds?: number
  reps?: number
  weight?: number
  rpe?: number
  notes?: string
}

async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  if (API_KEY) {
    headers['X-API-Key'] = API_KEY
  }

  const response = await fetch(url, { ...options, headers })

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

// Activity endpoints
export const getActivities = (limit = 30, type?: string): Promise<ActivityItem[]> =>
  fetchAPI(`/api/activities?limit=${limit}${type ? `&activity_type=${type}` : ''}`)

export const getCurrentWeekStats = (): Promise<WeekStats> =>
  fetchAPI('/api/stats/current-week')

/** Alias kept for backward compatibility with existing imports */
export const getStats = getCurrentWeekStats

export const getWeeklyStats = (weeks = 4): Promise<WeeklyStatEntry[]> =>
  fetchAPI(`/api/stats/weekly?weeks=${weeks}`)

export const getDailyData = (days = 30): Promise<DailyDataPoint[]> =>
  fetchAPI(`/api/daily?days=${days}`)

// CrossFit endpoints
export const getCrossFitWorkouts = (limit = 10): Promise<CrossFitWorkout[]> =>
  fetchAPI(`/api/crossfit/workouts?limit=${limit}`)

export const logCrossFitWorkout = (workout: CrossFitWorkoutInput): Promise<{ success: boolean; workout_id: number }> =>
  fetchAPI('/api/crossfit/log', {
    method: 'POST',
    body: JSON.stringify(workout),
  })

// Share card
export const getShareCard = (): Promise<ShareCardData> =>
  fetchAPI('/api/share/card')

// Health metrics
export const getLatestHealthMetrics = (): Promise<LatestHealthMetrics> =>
  fetchAPI('/api/health-metrics/latest')

export const getHealthMetricsHistory = (days = 30, metricType?: string): Promise<HealthMetric[]> =>
  fetchAPI(
    `/api/health-metrics/history?days=${days}${metricType ? `&metric_type=${encodeURIComponent(metricType)}` : ''}`
  )

export const getAppleHealthFormats = () =>
  fetchAPI('/api/apple-health/formats')
