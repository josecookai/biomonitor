const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE}${endpoint}`
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }
  
  return response.json()
}

// API Functions
export const getActivities = (limit = 30, type?: string) => 
  fetchAPI(`/api/activities?limit=${limit}${type ? `&activity_type=${type}` : ''}`)

export const getCurrentWeekStats = () => 
  fetchAPI('/api/stats/current-week')

export const getWeeklyStats = (weeks = 4) => 
  fetchAPI(`/api/stats/weekly?weeks=${weeks}`)

export const getDailyData = (days = 30) => 
  fetchAPI(`/api/daily?days=${days}`)

export const getCrossFitWorkouts = (limit = 10) => 
  fetchAPI(`/api/crossfit/workouts?limit=${limit}`)

export const logCrossFitWorkout = (workout: any) => 
  fetchAPI('/api/crossfit/log', {
    method: 'POST',
    body: JSON.stringify(workout),
  })

export const getShareCard = () => 
  fetchAPI('/api/share/card')

export const getLatestHealthMetrics = () =>
  fetchAPI('/api/health-metrics/latest')

export const getAppleHealthFormats = () =>
  fetchAPI('/api/apple-health/formats')
