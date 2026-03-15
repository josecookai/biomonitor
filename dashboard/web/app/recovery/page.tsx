'use client'

import { useEffect, useState } from 'react'
import { Heart, Moon, Activity, ArrowLeft, TrendingUp, TrendingDown, Loader2 } from 'lucide-react'
import Link from 'next/link'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts'
import {
  getLatestHealthMetrics,
  getHealthMetricsHistory,
  type LatestHealthMetrics,
  type HealthMetric
} from '@/lib/api'

function MetricCard({
  title,
  value,
  unit,
  icon: Icon,
  change,
  changeType
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
            <span className="text-2xl font-bold text-foreground">{value}</span>
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

function EmptyChartPlaceholder({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center h-[200px] rounded-lg bg-secondary/30 border border-dashed border-border">
      <p className="text-sm text-muted-foreground text-center px-4">{message}</p>
    </div>
  )
}

export default function RecoveryPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [latestMetrics, setLatestMetrics] = useState<LatestHealthMetrics | null>(null)
  const [hrvHistory, setHrvHistory] = useState<{ date: string; value: number }[]>([])

  useEffect(() => {
    async function loadData() {
      try {
        const [latest, hrvRecords] = await Promise.all([
          getLatestHealthMetrics(),
          getHealthMetricsHistory(30, 'HeartRateVariability')
        ])

        setLatestMetrics(latest)
        setHrvHistory(
          hrvRecords.map((record: HealthMetric) => ({
            date: record.date,
            value: record.value
          }))
        )
      } catch (err) {
        console.error('Failed to load recovery metrics:', err)
        setError('Failed to load recovery data. Please check your connection and try again.')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  const restingHr = latestMetrics?.resting_hr ?? null
  const hrv = latestMetrics?.hrv ?? null

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
              <p className="text-sm text-muted-foreground">Heart rate, HRV, and sleep analysis</p>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center max-w-md">
              <p className="text-muted-foreground">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition"
              >
                Retry
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Key Recovery Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <MetricCard
                title="Resting Heart Rate"
                value={restingHr !== null ? restingHr : '--'}
                unit="bpm"
                icon={Heart}
                change={restingHr !== null ? 'From Apple Health' : 'No data yet'}
                changeType="neutral"
              />
              <MetricCard
                title="HRV (Latest)"
                value={hrv !== null ? hrv : '--'}
                unit="ms"
                icon={Activity}
                change={hrv !== null ? 'From Apple Health' : 'No data yet'}
                changeType="neutral"
              />
              <MetricCard
                title="Sleep"
                value="--"
                unit="hrs"
                icon={Moon}
                change="Connect Apple Health"
                changeType="neutral"
              />
            </div>

            {/* Heart Rate Chart */}
            <div className="bg-card rounded-xl p-6 border border-border mb-6">
              <h3 className="text-lg font-semibold text-foreground mb-6">Heart Rate Zones</h3>
              <EmptyChartPlaceholder message="Connect Apple Health to populate this chart" />
            </div>

            {/* HRV Trend */}
            <div className="bg-card rounded-xl p-6 border border-border mb-6">
              <h3 className="text-lg font-semibold text-foreground mb-6">HRV Trend (30 Days)</h3>
              {hrvHistory.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={hrvHistory}>
                    <defs>
                      <linearGradient id="hrvRecovery" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} domain={['auto', 'auto']} />
                    <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }} />
                    <Area type="monotone" dataKey="value" stroke="#10b981" fill="url(#hrvRecovery)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <EmptyChartPlaceholder message="Connect Apple Health to populate this chart" />
              )}
            </div>

            {/* Sleep Analysis */}
            <div className="bg-card rounded-xl p-6 border border-border">
              <h3 className="text-lg font-semibold text-foreground mb-6">Sleep Analysis</h3>
              <EmptyChartPlaceholder message="Connect Apple Health to populate this chart" />
            </div>
          </>
        )}
      </div>
    </main>
  )
}
