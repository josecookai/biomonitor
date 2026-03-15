'use client'

import { useEffect, useState } from 'react'
import {
  Pill,
  ArrowLeft,
  Loader2,
  Sun,
  Moon,
  Zap,
  Activity,
  Coffee,
  AlertCircle,
  DollarSign,
  Clock,
} from 'lucide-react'
import Link from 'next/link'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || ''

// ------------------------------------------------------------------
// Types
// ------------------------------------------------------------------

interface SupplementItem {
  name: string
  dose: string
  timing: string
  reason: string
  evidence_level: 'strong' | 'moderate' | 'emerging'
  priority: 'essential' | 'recommended' | 'optional'
  contraindications: string[]
}

interface DailyPlanGroup {
  [key: string]: SupplementItem[]
}

interface DailyPlanMeta {
  total_supplements: number
  estimated_monthly_cost_usd: number
}

type DailyPlan = DailyPlanGroup & DailyPlanMeta

interface DailyPlanResponse {
  user_id: string
  name: string
  device: string
  health_goals: string[]
  recovery_score: number | null
  avg_sleep_hours: number | null
  avg_hrv: number | null
  plan: DailyPlan
}

// ------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------

async function fetchAPI<T>(endpoint: string): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (API_KEY) headers['X-API-Key'] = API_KEY
  const res = await fetch(`${API_BASE}${endpoint}`, { headers })
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`)
  return res.json()
}

const getUserDailyPlan = (userId: string): Promise<DailyPlanResponse> =>
  fetchAPI(`/api/users/${userId}/supplements/daily-plan`)

// ------------------------------------------------------------------
// Sub-components
// ------------------------------------------------------------------

const TIMING_CONFIG: Record<string, { label: string; icon: any; color: string; bg: string }> = {
  morning: {
    label: 'Morning Stack',
    icon: Sun,
    color: 'text-amber-500',
    bg: 'bg-amber-500/10',
  },
  pre_workout: {
    label: 'Pre-Workout',
    icon: Zap,
    color: 'text-blue-500',
    bg: 'bg-blue-500/10',
  },
  post_workout: {
    label: 'Post-Workout',
    icon: Activity,
    color: 'text-green-500',
    bg: 'bg-green-500/10',
  },
  evening: {
    label: 'Evening Stack',
    icon: Moon,
    color: 'text-purple-500',
    bg: 'bg-purple-500/10',
  },
  with_meal: {
    label: 'With Meal',
    icon: Coffee,
    color: 'text-orange-500',
    bg: 'bg-orange-500/10',
  },
}

const EVIDENCE_BADGES: Record<string, { label: string; classes: string }> = {
  strong:   { label: 'Strong evidence',   classes: 'bg-green-500/15 text-green-600 border-green-500/30' },
  moderate: { label: 'Moderate evidence', classes: 'bg-yellow-500/15 text-yellow-600 border-yellow-500/30' },
  emerging: { label: 'Emerging evidence', classes: 'bg-gray-500/15 text-gray-500 border-gray-500/30' },
}

const PRIORITY_BADGES: Record<string, { label: string; classes: string }> = {
  essential:   { label: 'Essential',   classes: 'bg-red-500/10 text-red-500' },
  recommended: { label: 'Recommended', classes: 'bg-blue-500/10 text-blue-500' },
  optional:    { label: 'Optional',    classes: 'bg-gray-500/10 text-gray-500' },
}

function SupplementCard({ supp }: { supp: SupplementItem }) {
  const evidence = EVIDENCE_BADGES[supp.evidence_level] ?? EVIDENCE_BADGES.emerging
  const priority = PRIORITY_BADGES[supp.priority] ?? PRIORITY_BADGES.optional

  return (
    <div className="bg-card border border-border rounded-xl p-5 flex flex-col gap-3 hover:border-primary/40 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-lg font-bold text-foreground leading-tight">{supp.name}</p>
          <p className="text-2xl font-semibold text-primary mt-0.5">{supp.dose}</p>
        </div>
        <span className={`text-xs font-medium px-2 py-1 rounded-full shrink-0 ${priority.classes}`}>
          {priority.label}
        </span>
      </div>
      <p className="text-sm text-muted-foreground">{supp.reason}</p>
      <div className="flex flex-wrap gap-2 mt-auto">
        <span className={`text-xs px-2 py-0.5 rounded border ${evidence.classes}`}>
          {evidence.label}
        </span>
      </div>
    </div>
  )
}

function TimingSection({
  timingKey,
  items,
}: {
  timingKey: string
  items: SupplementItem[]
}) {
  if (!items || items.length === 0) return null

  const config = TIMING_CONFIG[timingKey] ?? {
    label: timingKey,
    icon: Clock,
    color: 'text-muted-foreground',
    bg: 'bg-secondary',
  }
  const Icon = config.icon

  return (
    <section>
      <div className={`flex items-center gap-3 mb-4 p-3 rounded-xl ${config.bg}`}>
        <Icon className={`w-5 h-5 ${config.color}`} />
        <h3 className={`font-semibold text-base ${config.color}`}>{config.label}</h3>
        <span className="ml-auto text-xs text-muted-foreground">{items.length} supplement{items.length !== 1 ? 's' : ''}</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((s) => (
          <SupplementCard key={s.name} supp={s} />
        ))}
      </div>
    </section>
  )
}

function RecoveryBadge({ score }: { score: number | null }) {
  if (score === null) {
    return (
      <span className="px-3 py-1 rounded-full text-xs bg-secondary text-muted-foreground">
        Recovery: No data
      </span>
    )
  }

  let colorClass = 'bg-green-500/15 text-green-600'
  let label = 'Good'
  if (score < 40) { colorClass = 'bg-red-500/15 text-red-600'; label = 'Poor' }
  else if (score < 60) { colorClass = 'bg-yellow-500/15 text-yellow-600'; label = 'Fair' }

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${colorClass}`}>
      Recovery {score.toFixed(0)} — {label}
    </span>
  )
}

// ------------------------------------------------------------------
// Page
// ------------------------------------------------------------------

const USERS = [
  { id: 'carl',    label: 'Carl' },
  { id: 'zelda',   label: 'Zelda' },
  { id: 'zn',      label: 'ZN' },
  { id: 'default', label: 'Me' },
]

const TIMING_ORDER = ['morning', 'pre_workout', 'post_workout', 'evening', 'with_meal']

export default function SupplementsPage() {
  const [selectedUser, setSelectedUser] = useState<string>('carl')
  const [data, setData] = useState<DailyPlanResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    setData(null)

    getUserDailyPlan(selectedUser)
      .then(setData)
      .catch((err) => setError(err.message ?? 'Failed to load supplements'))
      .finally(() => setLoading(false))
  }, [selectedUser])

  const plan = data?.plan

  return (
    <main className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-4">
            <Link href="/">
              <button className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition">
                <ArrowLeft className="w-4 h-4" />
                <span className="text-sm">Dashboard</span>
              </button>
            </Link>
            <div className="w-px h-5 bg-border" />
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-gradient-to-br from-teal-500 to-cyan-600 rounded-lg">
                <Pill className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-bold text-foreground">Supplement Recommendations</h1>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* User selector tabs */}
        <div className="flex gap-2 mb-8">
          {USERS.map((u) => (
            <button
              key={u.id}
              onClick={() => setSelectedUser(u.id)}
              className={`px-5 py-2 rounded-full text-sm font-medium transition-all ${
                selectedUser === u.id
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/70'
              }`}
            >
              {u.label}
            </button>
          ))}
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-32">
            <Loader2 className="w-10 h-10 animate-spin text-muted-foreground" />
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="flex flex-col items-center gap-4 py-24 text-center">
            <div className="p-4 bg-red-500/10 rounded-full">
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>
            <div>
              <p className="font-semibold text-foreground mb-1">Failed to load recommendations</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
            <p className="text-xs text-muted-foreground">Connect your device to get personalised recommendations</p>
          </div>
        )}

        {/* Content */}
        {!loading && !error && data && plan && (
          <>
            {/* User summary bar */}
            <div className="flex flex-wrap items-center gap-3 mb-8 p-4 bg-card border border-border rounded-2xl">
              <div>
                <p className="text-lg font-bold text-foreground">{data.name}</p>
                <p className="text-sm text-muted-foreground capitalize">
                  {data.device.replace('_', ' ')} &nbsp;·&nbsp;
                  {data.health_goals.join(', ')}
                </p>
              </div>
              <div className="ml-auto flex flex-wrap items-center gap-2">
                <RecoveryBadge score={data.recovery_score} />
                {data.avg_sleep_hours !== null && (
                  <span className="px-3 py-1 rounded-full text-xs bg-secondary text-muted-foreground">
                    Sleep {data.avg_sleep_hours}h avg
                  </span>
                )}
                {data.avg_hrv !== null && (
                  <span className="px-3 py-1 rounded-full text-xs bg-secondary text-muted-foreground">
                    HRV {data.avg_hrv} ms avg
                  </span>
                )}
              </div>
            </div>

            {/* Empty state when no supplements */}
            {plan.total_supplements === 0 ? (
              <div className="flex flex-col items-center gap-4 py-24 text-center">
                <div className="p-4 bg-secondary rounded-full">
                  <Pill className="w-8 h-8 text-muted-foreground" />
                </div>
                <p className="font-semibold text-foreground">No recommendations yet</p>
                <p className="text-sm text-muted-foreground">Connect your device to get personalised supplement recommendations</p>
              </div>
            ) : (
              <>
                {/* Timeline sections */}
                <div className="flex flex-col gap-10">
                  {TIMING_ORDER.map((key) => {
                    const items = plan[key] as SupplementItem[] | undefined
                    return (
                      <TimingSection
                        key={key}
                        timingKey={key}
                        items={items ?? []}
                      />
                    )
                  })}
                </div>

                {/* Cost summary */}
                <div className="mt-10 flex items-center gap-3 p-5 bg-card border border-border rounded-2xl">
                  <div className="p-2.5 bg-green-500/10 rounded-xl">
                    <DollarSign className="w-5 h-5 text-green-500" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Estimated monthly cost</p>
                    <p className="text-2xl font-bold text-foreground">
                      ${plan.estimated_monthly_cost_usd}
                      <span className="text-sm font-normal text-muted-foreground ml-1">/ month</span>
                    </p>
                  </div>
                  <div className="ml-auto text-right">
                    <p className="text-sm text-muted-foreground">Total supplements</p>
                    <p className="text-2xl font-bold text-foreground">{plan.total_supplements}</p>
                  </div>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </main>
  )
}
