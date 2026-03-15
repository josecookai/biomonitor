'use client'

import { useEffect, useState } from 'react'
import { Loader2, Moon, Droplets, Dumbbell, PersonStanding, Heart, BellRing } from 'lucide-react'
import Link from 'next/link'
import { fetchAPI } from '@/lib/api'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ScheduleItem {
  time: string
  type: 'hydration' | 'standing' | 'fitness' | 'sleep' | 'recovery' | string
  message: string
  priority: 'high' | 'medium' | 'low'
}

interface DailySchedule {
  date: string
  schedule: ScheduleItem[]
  recovery_color: 'green' | 'yellow' | 'red'
  recovery_score: number
}

interface RecoveryData {
  recovery_score: number
  recommendation: 'workout' | 'rest' | 'light'
  color: 'green' | 'yellow' | 'red'
  factors: string[]
  data_available: boolean
}

interface SleepData {
  recommended_bedtime: string
  recommended_wake: string
  target_hours: number
  current_avg_hours: number | null
  reason: string
  priority: 'high' | 'medium' | 'low'
}

interface FitnessData {
  sessions_this_week: number
  target: number
  next_recommended: string
  today_recommendation: 'workout' | 'rest' | 'active_recovery'
  reason: string
  suggested_time: string
  days_since_last_workout: number | null
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const typeIcon: Record<string, string> = {
  hydration: '💧',
  standing: '🧍',
  fitness: '🏋️',
  sleep: '😴',
  recovery: '💚',
}

const priorityBorder: Record<string, string> = {
  high: 'border-l-red-500',
  medium: 'border-l-yellow-500',
  low: 'border-l-green-500',
}

const recoveryColorMap: Record<string, string> = {
  green: 'bg-green-500',
  yellow: 'bg-yellow-400',
  red: 'bg-red-500',
}

const recoveryRingMap: Record<string, string> = {
  green: 'ring-green-500',
  yellow: 'ring-yellow-400',
  red: 'ring-red-500',
}

const recoveryTextMap: Record<string, string> = {
  green: 'text-green-500',
  yellow: 'text-yellow-500',
  red: 'text-red-500',
}

function getReminders(params?: Record<string, string>) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : ''
  return fetchAPI<DailySchedule>(`/api/reminders/daily${qs}`)
}

function getRecovery() {
  return fetchAPI<RecoveryData>('/api/reminders/recovery')
}

function getSleepRecommendation() {
  return fetchAPI<SleepData>('/api/reminders/sleep')
}

function getFitnessReminders(weeklyTarget = 3) {
  return fetchAPI<FitnessData>(`/api/reminders/fitness?weekly_target=${weeklyTarget}`)
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function RecoveryScoreCard({ data, loading }: { data: RecoveryData | null; loading: boolean }) {
  if (loading) {
    return (
      <div className="bg-card rounded-2xl p-8 border border-border flex items-center justify-center h-48">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  if (!data) return null

  const ringColor = recoveryRingMap[data.color] ?? 'ring-gray-400'
  const textColor = recoveryTextMap[data.color] ?? 'text-gray-500'
  const label = data.recommendation === 'workout'
    ? 'Go Hard'
    : data.recommendation === 'light'
    ? 'Light Activity'
    : 'Rest Day'

  return (
    <div className="bg-card rounded-2xl p-8 border border-border">
      <div className="flex items-center gap-3 mb-6">
        <Heart className="w-5 h-5 text-red-500" />
        <h2 className="text-lg font-semibold text-foreground">Recovery Score</h2>
        {!data.data_available && (
          <span className="ml-auto text-xs text-muted-foreground bg-secondary px-2 py-1 rounded">
            No data — estimated
          </span>
        )}
      </div>
      <div className="flex items-center gap-8">
        <div className={`ring-4 ${ringColor} rounded-full w-28 h-28 flex flex-col items-center justify-center shrink-0`}>
          <span className={`text-4xl font-bold ${textColor}`}>{data.recovery_score}</span>
          <span className="text-xs text-muted-foreground">/100</span>
        </div>
        <div>
          <p className={`text-2xl font-semibold ${textColor} mb-2`}>{label}</p>
          <ul className="space-y-1">
            {data.factors.map((f, i) => (
              <li key={i} className="text-sm text-muted-foreground">• {f}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}

function ScheduleTimeline({ items, loading }: { items: ScheduleItem[]; loading: boolean }) {
  if (loading) {
    return (
      <div className="bg-card rounded-2xl p-8 border border-border flex items-center justify-center h-48">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  if (!items.length) {
    return (
      <div className="bg-card rounded-2xl p-8 border border-border text-center text-muted-foreground">
        No schedule items. Connect your health devices to get personalised reminders.
      </div>
    )
  }

  return (
    <div className="bg-card rounded-2xl border border-border overflow-hidden">
      <div className="px-6 py-4 border-b border-border flex items-center gap-3">
        <BellRing className="w-5 h-5 text-primary" />
        <h2 className="text-lg font-semibold text-foreground">Today's Schedule</h2>
      </div>
      <div className="divide-y divide-border">
        {items.map((item, i) => (
          <div
            key={i}
            className={`flex items-start gap-4 px-6 py-4 border-l-4 ${priorityBorder[item.priority] ?? 'border-l-border'}`}
          >
            <span className="text-2xl mt-0.5">{typeIcon[item.type] ?? '🔔'}</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-foreground leading-snug">{item.message}</p>
              <p className="text-xs text-muted-foreground mt-1 capitalize">{item.type}</p>
            </div>
            <span className="text-sm font-mono font-medium text-muted-foreground shrink-0 mt-0.5">
              {item.time}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function SleepCard({ data, loading }: { data: SleepData | null; loading: boolean }) {
  if (loading) {
    return (
      <div className="bg-card rounded-2xl p-6 border border-border flex items-center justify-center h-40">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    )
  }

  const empty = !data

  return (
    <div className="bg-card rounded-2xl p-6 border border-border">
      <div className="flex items-center gap-3 mb-4">
        <Moon className="w-5 h-5 text-purple-500" />
        <h3 className="text-base font-semibold text-foreground">Sleep</h3>
        {data && (
          <span className={`ml-auto text-xs font-medium px-2 py-0.5 rounded-full ${
            data.priority === 'high' ? 'bg-red-500/15 text-red-500'
            : data.priority === 'medium' ? 'bg-yellow-500/15 text-yellow-500'
            : 'bg-green-500/15 text-green-500'
          }`}>
            {data.priority}
          </span>
        )}
      </div>
      {empty ? (
        <p className="text-sm text-muted-foreground">No sleep data yet</p>
      ) : (
        <>
          <div className="flex justify-between mb-3">
            <div className="text-center">
              <p className="text-xs text-muted-foreground mb-1">Current avg</p>
              <p className="text-2xl font-bold text-foreground">
                {data.current_avg_hours !== null ? `${data.current_avg_hours}h` : '—'}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground mb-1">Target</p>
              <p className="text-2xl font-bold text-foreground">{data.target_hours}h</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground mb-1">Bedtime</p>
              <p className="text-2xl font-bold text-foreground">{data.recommended_bedtime}</p>
            </div>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">{data.reason}</p>
        </>
      )}
    </div>
  )
}

function HydrationCard({ glasses, loading }: { glasses: number; loading: boolean }) {
  const total = 8
  const filled = Math.min(glasses, total)

  if (loading) {
    return (
      <div className="bg-card rounded-2xl p-6 border border-border flex items-center justify-center h-40">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    )
  }

  return (
    <div className="bg-card rounded-2xl p-6 border border-border">
      <div className="flex items-center gap-3 mb-4">
        <Droplets className="w-5 h-5 text-blue-500" />
        <h3 className="text-base font-semibold text-foreground">Hydration</h3>
        <span className="ml-auto text-sm font-medium text-muted-foreground">{filled}/{total} glasses</span>
      </div>
      <div className="flex gap-2 flex-wrap mb-3">
        {Array.from({ length: total }).map((_, i) => (
          <div
            key={i}
            className={`w-8 h-10 rounded-b-xl rounded-t-sm border-2 transition-colors ${
              i < filled
                ? 'bg-blue-500 border-blue-600'
                : 'bg-secondary border-border'
            }`}
          />
        ))}
      </div>
      <p className="text-xs text-muted-foreground">
        {filled === 0
          ? 'No glasses logged yet — stay hydrated!'
          : filled >= total
          ? 'Daily hydration goal reached!'
          : `${total - filled} more glass${total - filled !== 1 ? 'es' : ''} to go`}
      </p>
    </div>
  )
}

function FitnessCard({ data, loading }: { data: FitnessData | null; loading: boolean }) {
  if (loading) {
    return (
      <div className="bg-card rounded-2xl p-6 border border-border flex items-center justify-center h-40">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    )
  }

  const empty = !data

  return (
    <div className="bg-card rounded-2xl p-6 border border-border">
      <div className="flex items-center gap-3 mb-4">
        <Dumbbell className="w-5 h-5 text-orange-500" />
        <h3 className="text-base font-semibold text-foreground">Fitness</h3>
      </div>
      {empty ? (
        <p className="text-sm text-muted-foreground">No fitness data yet</p>
      ) : (
        <>
          <div className="flex justify-between mb-3">
            <div className="text-center">
              <p className="text-xs text-muted-foreground mb-1">This week</p>
              <p className="text-2xl font-bold text-foreground">
                {data.sessions_this_week}/{data.target}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground mb-1">Next session</p>
              <p className="text-sm font-bold text-foreground">{data.next_recommended}</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground mb-1">Today</p>
              <p className={`text-sm font-bold capitalize ${
                data.today_recommendation === 'workout'
                  ? 'text-green-500'
                  : data.today_recommendation === 'rest'
                  ? 'text-red-500'
                  : 'text-yellow-500'
              }`}>
                {data.today_recommendation.replace('_', ' ')}
              </p>
            </div>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">{data.reason}</p>
        </>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function RemindersPage() {
  const [schedule, setSchedule] = useState<DailySchedule | null>(null)
  const [recovery, setRecovery] = useState<RecoveryData | null>(null)
  const [sleepData, setSleepData] = useState<SleepData | null>(null)
  const [fitnessData, setFitnessData] = useState<FitnessData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [sched, rec, slp, fit] = await Promise.all([
          getReminders(),
          getRecovery(),
          getSleepRecommendation(),
          getFitnessReminders(),
        ])
        setSchedule(sched)
        setRecovery(rec)
        setSleepData(slp)
        setFitnessData(fit)
      } catch (err) {
        console.error('Failed to load reminders:', err)
        setError('Failed to load reminders. Please check your API connection.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  const dotColor = recovery
    ? recoveryColorMap[recovery.color] ?? 'bg-gray-400'
    : 'bg-gray-300'

  return (
    <main className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
                <BellRing className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">Smart Reminders</h1>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${dotColor}`} />
                  <p className="text-sm text-muted-foreground">{today}</p>
                </div>
              </div>
            </div>
            <Link href="/">
              <button className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition text-sm">
                ← Dashboard
              </button>
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-500 text-sm">
            {error}
          </div>
        )}

        {/* Recovery Score */}
        <RecoveryScoreCard data={recovery} loading={loading} />

        {/* Today's full schedule */}
        <ScheduleTimeline items={schedule?.schedule ?? []} loading={loading} />

        {/* Three info cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <SleepCard data={sleepData} loading={loading} />
          <HydrationCard glasses={0} loading={loading} />
          <FitnessCard data={fitnessData} loading={loading} />
        </div>

        <footer className="pt-6 border-t border-border text-center">
          <p className="text-muted-foreground text-sm">
            BioMonitor — Smart Reminders powered by Apple Watch, WHOOP & Oura data
          </p>
        </footer>
      </div>
    </main>
  )
}
