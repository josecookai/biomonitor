'use client'

import { useEffect, useState } from 'react'
import { Heart, Moon, Activity, ArrowLeft, TrendingUp, TrendingDown } from 'lucide-react'
import Link from 'next/link'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts'
import { getAppleHealthFormats, getLatestHealthMetrics } from '@/lib/api'

const hrData = [
  { day: 'Mon', resting: 72, max: 165 },
  { day: 'Tue', resting: 68, max: 158 },
  { day: 'Wed', resting: 75, max: 172 },
  { day: 'Thu', resting: 70, max: 155 },
  { day: 'Fri', resting: 73, max: 168 },
  { day: 'Sat', resting: 65, max: 145 },
  { day: 'Sun', resting: 68, max: 150 },
]

const sleepData = [
  { day: 'Mon', hours: 7.5, deep: 1.5 },
  { day: 'Tue', hours: 6.8, deep: 1.2 },
  { day: 'Wed', hours: 7.2, deep: 1.8 },
  { day: 'Thu', hours: 7.0, deep: 1.4 },
  { day: 'Fri', hours: 6.5, deep: 1.1 },
  { day: 'Sat', hours: 8.0, deep: 2.0 },
  { day: 'Sun', hours: 8.2, deep: 2.1 },
]

const hrvTrend = [
  { date: '1', value: 42 },
  { date: '5', value: 44 },
  { date: '10', value: 48 },
  { date: '15', value: 52 },
  { date: '20', value: 49 },
  { date: '25', value: 51 },
  { date: '30', value: 53 },
]

function MetricCard({
  title,
  value,
  unit,
  icon: Icon,
  change,
  changeType,
}: {
  title: string
  value: string | number
  unit: string
  icon: any
  change: string
  changeType: 'up' | 'down' | 'neutral'
}) {
  return (
    <div className="bg-card rounded-xl p-6 border border-border">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-muted-foreground text-sm">{title}</p>
          <div className="flex items-baseline gap-1 mt-2">
            <span className="text-2xl font-bold text-foreground font-mono-display">{value}</span>
            <span className="text-muted-foreground text-sm">{unit}</span>
          </div>
          <div className={`flex items-center gap-1 mt-1 text-sm ${
            changeType === 'up' ? 'text-green-500' :
            changeType === 'down' ? 'text-red-500' : 'text-muted-foreground'
          }`}>
            {changeType === 'up' && <TrendingUp className="w-3 h-3" />}
            {changeType === 'down' && <TrendingDown className="w-3 h-3" />}
            <span>{change}</span>
          </div>
        </div>
        <div className="p-3 bg-secondary rounded-lg">
          <Icon className="w-5 h-5 text-foreground" />
        </div>
      </div>
    </div>
  )
}

export default function RecoveryPage() {
  const [healthMetrics, setHealthMetrics] = useState<any>(null)
  const [formats, setFormats] = useState<any[]>([])

  useEffect(() => {
    async function loadHealthData() {
      try {
        const [latest, formatData] = await Promise.all([
          getLatestHealthMetrics(),
          getAppleHealthFormats(),
        ])
        setHealthMetrics(latest)
        setFormats(formatData.supported_metrics || [])
      } catch (error) {
        console.error('Failed to load recovery data:', error)
      }
    }

    loadHealthData()
  }, [])

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-4">
            <Link href="/" className="p-2 hover:bg-secondary rounded-lg transition">
              <ArrowLeft className="w-5 h-5 text-muted-foreground" />
            </Link>
            <div>
              <h1 className="text-xl font-bold text-foreground">Recovery Metrics</h1>
              <p className="text-sm text-muted-foreground">Heart rate, HRV, sleep, rings and Apple Watch payloads</p>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <MetricCard title="Resting Heart Rate" value={healthMetrics?.resting_hr || 70} unit="bpm" icon={Heart} change="-2 bpm vs last week" changeType="up" />
          <MetricCard title="HRV (Avg)" value={healthMetrics?.hrv || 48} unit="ms" icon={Activity} change="+5 ms vs last week" changeType="up" />
          <MetricCard title="Sleep Score" value={healthMetrics?.recovery_score || 82} unit="/100" icon={Moon} change="-3 pts vs last week" changeType="down" />
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          {[
            ['Steps', healthMetrics?.steps || 8500, 'steps'],
            ['Active Energy', healthMetrics?.active_energy_kcal || 684, 'kcal'],
            ['Exercise', healthMetrics?.exercise_minutes || 57, 'min'],
            ['Blood Oxygen', healthMetrics?.blood_oxygen || 98, '%'],
            ['VO2 Max', healthMetrics?.vo2_max || 47.6, 'ml/kg/min'],
            ['Stand Hours', healthMetrics?.stand_hours || 11, 'hrs'],
            ['Resp Rate', healthMetrics?.respiratory_rate || 15.8, '/min'],
            ['Wrist Temp', healthMetrics?.wrist_temperature_delta || 0.2, 'delta C'],
            ['Mindfulness', healthMetrics?.mindfulness_minutes || 10, 'min'],
            ['Sync', healthMetrics?.source || 'apple_health', 'source'],
          ].map(([label, value, unit]) => (
            <div key={String(label)} className="bg-card rounded-xl p-4 border border-border">
              <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
              <p className="text-2xl font-bold text-foreground mt-2 font-mono-display">{value}</p>
              <p className="text-sm text-muted-foreground mt-1">{unit}</p>
            </div>
          ))}
        </div>

        <div className="bg-card rounded-xl p-6 border border-border mb-6">
          <h3 className="text-lg font-semibold text-foreground mb-6">Heart Rate Zones</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={hrData}>
              <defs>
                <linearGradient id="maxHrGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="day" stroke="hsl(var(--muted-foreground))" fontSize={12} />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} domain={[40, 180]} />
              <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }} />
              <Area type="monotone" dataKey="max" stroke="#ef4444" fill="url(#maxHrGradient)" strokeWidth={2} />
              <Line type="monotone" dataKey="resting" stroke="#3b82f6" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-card rounded-xl p-6 border border-border mb-6">
          <h3 className="text-lg font-semibold text-foreground mb-6">HRV Trend (30 Days)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={hrvTrend}>
              <defs>
                <linearGradient id="hrvRecovery" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} domain={[30, 70]} />
              <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }} />
              <Area type="monotone" dataKey="value" stroke="#10b981" fill="url(#hrvRecovery)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-card rounded-xl p-6 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-6">Sleep Analysis</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={sleepData}>
              <defs>
                <linearGradient id="sleepGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="day" stroke="hsl(var(--muted-foreground))" fontSize={12} />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} domain={[0, 10]} />
              <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }} />
              <Area type="monotone" dataKey="hours" stroke="#f97316" fill="url(#sleepGradient)" strokeWidth={2} />
              <Line type="monotone" dataKey="deep" stroke="#84cc16" strokeWidth={2} strokeDasharray="5 5" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-card rounded-xl p-6 border border-border mt-6">
          <div className="flex items-center justify-between gap-4 mb-6">
            <div>
              <h3 className="text-lg font-semibold text-foreground">Apple Watch Data Formats</h3>
              <p className="text-sm text-muted-foreground">Health Auto Export compatible payload samples for dashboard and future ingestion pipelines.</p>
            </div>
            <span className="px-3 py-1 rounded-full bg-secondary text-xs uppercase tracking-[0.2em] text-muted-foreground">
              JSON shape
            </span>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {formats.map((metric) => (
              <div key={metric.healthkit_type} className="rounded-xl border border-border bg-background/50 p-4">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <h4 className="font-semibold text-foreground">{metric.name}</h4>
                    <p className="text-sm text-muted-foreground">{metric.healthkit_type}</p>
                  </div>
                  <span className="text-xs text-muted-foreground uppercase tracking-[0.18em]">{metric.unit}</span>
                </div>
                <pre className="text-xs leading-6 text-muted-foreground whitespace-pre-wrap break-words font-mono-display">
                  {JSON.stringify(metric.sample, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  )
}
