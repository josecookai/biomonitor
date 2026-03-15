'use client'

import { useEffect, useState } from 'react'
import {
  Activity,
  Dumbbell,
  Flame,
  Footprints,
  Heart,
  Loader2,
  Share2,
  TimerReset,
  Watch,
  Zap,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import Link from 'next/link'
import {
  getActivities,
  getCurrentWeekStats,
  getDailyData,
  getLatestHealthMetrics,
  getShareCard,
} from '@/lib/api'

function MetricCard({
  title,
  value,
  unit,
  icon: Icon,
  subtitle,
  loading,
}: {
  title: string
  value: string | number
  unit?: string
  icon: any
  subtitle?: string
  loading?: boolean
}) {
  return (
    <div className="bg-card/80 panel-glow rounded-[28px] p-6 border border-border">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="metric-kicker text-muted-foreground">{title}</p>
          {loading ? (
            <Loader2 className="w-6 h-6 animate-spin mt-3" />
          ) : (
            <div className="flex items-baseline gap-2 mt-3">
              <span className="text-3xl md:text-4xl font-bold text-foreground font-mono-display">{value}</span>
              {unit && <span className="text-muted-foreground text-sm md:text-base">{unit}</span>}
            </div>
          )}
          {subtitle && !loading && <p className="text-sm mt-2 text-muted-foreground">{subtitle}</p>}
        </div>
        <div className="p-3 bg-secondary rounded-2xl">
          <Icon className="w-5 h-5 text-primary" />
        </div>
      </div>
    </div>
  )
}

function ActivityChart({ data, loading }: { data: any[]; loading: boolean }) {
  if (loading) {
    return (
      <div className="bg-card/80 panel-glow rounded-[28px] p-6 border border-border h-[350px] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="bg-card/80 panel-glow rounded-[28px] p-6 border border-border">
      <div className="flex items-center justify-between mb-6 gap-4">
        <div>
          <h3 className="text-lg font-semibold text-foreground">Activity Mix</h3>
          <p className="text-muted-foreground text-sm">CrossFit volume and walking distance over the last 7 days</p>
        </div>
        <div className="flex gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-orange-500 rounded-full" />
            <span className="text-sm text-muted-foreground">CrossFit</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full" />
            <span className="text-sm text-muted-foreground">Walking (km)</span>
          </div>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="day" stroke="hsl(var(--muted-foreground))" fontSize={12} />
          <YAxis yAxisId="left" stroke="hsl(var(--muted-foreground))" fontSize={12} allowDecimals={false} />
          <YAxis yAxisId="right" orientation="right" stroke="hsl(var(--muted-foreground))" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '16px',
            }}
          />
          <Bar yAxisId="left" dataKey="crossfit" fill="#f97316" radius={[8, 8, 0, 0]} />
          <Bar yAxisId="right" dataKey="walking" fill="#3b82f6" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<any>(null)
  const [activities, setActivities] = useState<any[]>([])
  const [dailyData, setDailyData] = useState<any[]>([])
  const [shareData, setShareData] = useState<any>(null)
  const [healthMetrics, setHealthMetrics] = useState<any>(null)

  useEffect(() => {
    async function loadData() {
      try {
        const [statsData, acts, daily, share, health] = await Promise.all([
          getCurrentWeekStats(),
          getActivities(10),
          getDailyData(7),
          getShareCard(),
          getLatestHealthMetrics(),
        ])

        setStats(statsData)
        setActivities(acts)
        setDailyData(
          daily.map((d: any) => {
            const date = new Date(d.date)
            return {
              day: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][date.getDay()],
              crossfit: d.crossfit,
              walking: d.walking,
            }
          })
        )
        setShareData(share)
        setHealthMetrics(health)
      } catch (error) {
        console.error('Failed to load data:', error)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  const recentActivities = activities.slice(0, 4)
  const totalExerciseMinutes = activities.reduce((sum, item) => sum + Math.round((item.moving_time || 0) / 60), 0)
  const totalCalories = activities.reduce((sum, item) => {
    const minutes = (item.moving_time || 0) / 60
    if (item.is_crossfit) return sum + minutes * 12
    if (item.is_walking) return sum + minutes * 4
    return sum + minutes * 6
  }, 0)

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-orange-500 to-lime-400 rounded-2xl">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">BioMonitor</h1>
                <p className="text-sm text-muted-foreground">Training and recovery signal board</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="hidden md:inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary text-sm text-muted-foreground">
                <Watch className="w-4 h-4 text-accent" />
                Apple Watch sync ready
              </span>
              <Link href="/share">
                <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-full hover:opacity-90 transition">
                  <Share2 className="w-4 h-4" />
                  <span className="text-sm font-medium">Share</span>
                </button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <section className="mb-8 rounded-[36px] border border-border bg-card/70 panel-glow overflow-hidden">
          <div className="grid lg:grid-cols-[1.4fr_0.9fr] gap-8 p-6 md:p-8">
            <div>
              <p className="metric-kicker text-muted-foreground mb-3">This Week</p>
              <h2 className="text-4xl md:text-6xl font-bold text-foreground max-w-3xl">
                Track workload, recovery and Apple Watch signals in one demo-ready dashboard.
              </h2>
              <p className="text-muted-foreground text-base md:text-lg mt-4 max-w-2xl">
                Week of {stats?.week_start || new Date().toLocaleDateString()} with CrossFit, walks, recovery and wearable inputs ready for demo flow.
              </p>
              <div className="flex flex-wrap gap-3 mt-6">
                <Link href="/activity" className="px-5 py-3 rounded-full bg-white text-black text-sm font-medium hover:opacity-90 transition">
                  View Activity
                </Link>
                <Link href="/recovery" className="px-5 py-3 rounded-full bg-secondary text-foreground text-sm font-medium hover:bg-secondary/80 transition">
                  Explore Recovery
                </Link>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 self-start">
              <MetricCard title="Total Duration" value={loading ? 0 : totalExerciseMinutes} unit="min" icon={TimerReset} subtitle="All tracked sessions" loading={loading} />
              <MetricCard title="Workout Count" value={loading ? 0 : activities.length} unit="sessions" icon={Zap} subtitle="Movement events this cycle" loading={loading} />
              <MetricCard title="Active Energy" value={loading ? 0 : Math.round(totalCalories)} unit="kcal" icon={Flame} subtitle="Estimated from session type" loading={loading} />
              <MetricCard title="Recovery Score" value={healthMetrics?.recovery_score || 82} unit="/100" icon={Heart} subtitle="Apple Watch derived" loading={loading} />
            </div>
          </div>
        </section>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
          <MetricCard title="CrossFit Sessions" value={stats?.crossfit_sessions || 0} unit="/ week" icon={Dumbbell} subtitle={stats?.crossfit_sessions >= 3 ? 'Target hit' : `${3 - (stats?.crossfit_sessions || 0)} to goal`} loading={loading} />
          <MetricCard title="Walking Distance" value={stats?.walking_distance_km?.toFixed(1) || 0} unit="km" icon={Footprints} subtitle="Low intensity base work" loading={loading} />
          <MetricCard title="Avg Resting HR" value={healthMetrics?.resting_hr || shareData?.resting_hr || 70} unit="bpm" icon={Heart} subtitle="Latest Apple Watch sync" loading={loading} />
          <MetricCard title="Exercise Minutes" value={healthMetrics?.exercise_minutes || Math.round((stats?.walking_time_min || 0) * 1.5)} unit="min" icon={Watch} subtitle="Apple Watch exercise ring" loading={loading} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2">
            <ActivityChart data={dailyData} loading={loading} />
          </div>
          <div className="lg:col-span-1">
            <Link href="/recovery">
              <div className="bg-card/80 panel-glow rounded-[28px] p-6 border border-border h-full hover:border-primary transition cursor-pointer">
                <h3 className="text-lg font-semibold text-foreground mb-4">Apple Watch Snapshot</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">HRV</span>
                    <span className="font-bold font-mono-display">{healthMetrics?.hrv || shareData?.hrv || 49} ms</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Resting HR</span>
                    <span className="font-bold font-mono-display">{healthMetrics?.resting_hr || shareData?.resting_hr || 70} bpm</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Sleep</span>
                    <span className="font-bold font-mono-display">{healthMetrics?.sleep_hours || 7.2} h</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Blood Oxygen</span>
                    <span className="font-bold font-mono-display">{healthMetrics?.blood_oxygen || 98}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Active Energy</span>
                    <span className="font-bold font-mono-display">{healthMetrics?.active_energy_kcal || 684} kcal</span>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mt-6">Click for detailed metrics and data formats →</p>
              </div>
            </Link>
          </div>
        </div>

        <div className="bg-card/80 panel-glow rounded-[28px] p-6 border border-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-foreground">Recent Activities</h3>
            <Link href="/activity">
              <span className="text-sm text-primary hover:underline">View all →</span>
            </Link>
          </div>

          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
          ) : recentActivities.length > 0 ? (
            <div className="space-y-4">
              {recentActivities.map((activity, i) => (
                <div key={i} className="flex items-center justify-between py-3 border-b border-border last:border-0">
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-2xl ${activity.is_crossfit ? 'bg-orange-500/20' : activity.is_walking ? 'bg-blue-500/20' : 'bg-secondary'}`}>
                      {activity.is_crossfit ? (
                        <Dumbbell className="w-4 h-4 text-orange-500" />
                      ) : activity.is_walking ? (
                        <Footprints className="w-4 h-4 text-blue-500" />
                      ) : (
                        <Activity className="w-4 h-4" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-foreground">{activity.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {activity.type} • {new Date(activity.start_date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <span className="text-sm font-medium text-foreground font-mono-display">{Math.round(activity.moving_time / 60)} min</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">No activities yet. Sync your data.</p>
          )}
        </div>

        <footer className="mt-12 pt-8 border-t border-border text-center">
          <p className="text-muted-foreground text-sm">
            BioMonitor v0.1.0 • Data from Apple Watch, Strava and future wellness connectors
          </p>
        </footer>
      </div>
    </main>
  )
}
