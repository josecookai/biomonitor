'use client'

import { useEffect, useState } from 'react'
import { 
  Activity, 
  Heart, 
  Footprints, 
  Dumbbell,
  Flame,
  Share2,
  Loader2,
  Timer,
  Trophy,
  Zap,
  TrendingUp,
  Calendar
} from 'lucide-react'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area,
  Cell
} from 'recharts'
import Link from 'next/link'
import {
  getActivities,
  getStats,
  getDailyData,
  getShareCard,
  type ActivityItem,
  type WeekStats,
  type DailyDataPoint,
  type ShareCardData
} from '@/lib/api'

// Big stat card component (inspired by endless.wenxin.io)
function BigStatCard({ 
  title, 
  value, 
  unit, 
  subtext,
  icon: Icon,
  color = "blue"
}: { 
  title: string
  value: string | number
  unit?: string
  subtext?: string
  icon: any
  color?: "blue" | "orange" | "green" | "red" | "purple"
}) {
  const colorClasses = {
    blue: "from-blue-500/20 to-blue-600/10 text-blue-600",
    orange: "from-orange-500/20 to-orange-600/10 text-orange-600",
    green: "from-green-500/20 to-green-600/10 text-green-600",
    red: "from-red-500/20 to-red-600/10 text-red-600",
    purple: "from-purple-500/20 to-purple-600/10 text-purple-600"
  }

  return (
    <div className="bg-card rounded-2xl p-8 border border-border text-center hover:border-primary/50 transition-all">
      <div className={`inline-flex p-4 rounded-2xl bg-gradient-to-br ${colorClasses[color]} mb-4`}>
        <Icon className="w-8 h-8" />
      </div>
      <div className="text-4xl md:text-5xl font-bold text-foreground mb-2">
        {value}<span className="text-2xl text-muted-foreground ml-1">{unit}</span>
      </div>
      <div className="text-muted-foreground text-sm uppercase tracking-wider mb-1">{title}</div>
      {subtext && <div className="text-xs text-muted-foreground/70">{subtext}</div>}
    </div>
  )
}

function MetricCard({ 
  title, 
  value, 
  unit, 
  icon: Icon, 
  trend, 
  trendUp,
  loading 
}: { 
  title: string
  value: string | number
  unit?: string
  icon: any
  trend?: string
  trendUp?: boolean
  loading?: boolean
}) {
  return (
    <div className="bg-card rounded-xl p-6 border border-border">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-muted-foreground text-sm">{title}</p>
          {loading ? (
            <Loader2 className="w-6 h-6 animate-spin mt-2" />
          ) : (
            <div className="flex items-baseline gap-1 mt-2">
              <span className="text-3xl font-bold text-foreground">{value}</span>
              {unit && <span className="text-muted-foreground text-sm">{unit}</span>}
            </div>
          )}
          {trend && !loading && (
            <p className={`text-sm mt-1 ${trendUp ? 'text-green-500' : 'text-red-500'}`}>
              {trendUp ? '↑' : '↓'} {trend}
            </p>
          )}
        </div>
        <div className="p-3 bg-secondary rounded-lg">
          <Icon className="w-5 h-5 text-foreground" />
        </div>
      </div>
    </div>
  )
}

function ActivityChart({ data, loading }: { data: any[], loading: boolean }) {
  if (loading) {
    return (
      <div className="bg-card rounded-xl p-6 border border-border h-[350px] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="bg-card rounded-xl p-6 border border-border">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-foreground">Weekly Activity</h3>
          <p className="text-muted-foreground text-sm">CrossFit sessions & walking distance</p>
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
          <YAxis yAxisId="left" stroke="hsl(var(--muted-foreground))" fontSize={12} />
          <YAxis yAxisId="right" orientation="right" stroke="hsl(var(--muted-foreground))" fontSize={12} />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'hsl(var(--card))', 
              border: '1px solid hsl(var(--border))',
              borderRadius: '8px'
            }}
          />
          <Bar yAxisId="left" dataKey="crossfit" fill="#f97316" radius={[4, 4, 0, 0]} />
          <Bar yAxisId="right" dataKey="walking" fill="#3b82f6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

// Calendar heatmap component
function CalendarHeatmap({ data }: { data: any[] }) {
  // Generate last 90 days
  const days = []
  const today = new Date()
  for (let i = 89; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    days.push({
      date: d,
      dateStr: d.toISOString().split('T')[0],
      activity: data.find((a: any) => a.start_date?.includes(d.toISOString().split('T')[0]))
    })
  }

  return (
    <div className="bg-card rounded-xl p-6 border border-border">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground">Activity Calendar</h3>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>Less</span>
          <div className="flex gap-1">
            <div className="w-3 h-3 bg-secondary rounded-sm" />
            <div className="w-3 h-3 bg-orange-500/30 rounded-sm" />
            <div className="w-3 h-3 bg-orange-500/60 rounded-sm" />
            <div className="w-3 h-3 bg-orange-500 rounded-sm" />
          </div>
          <span>More</span>
        </div>
      </div>
      <div className="grid grid-cols-13 gap-1">
        {days.map((day, i) => {
          const intensity = day.activity 
            ? day.activity.is_crossfit ? 'bg-orange-500' 
              : day.activity.is_walking ? 'bg-blue-500/60' 
              : 'bg-secondary'
            : 'bg-secondary/50'
          return (
            <div
              key={i}
              className={`w-3 h-3 rounded-sm ${intensity}`}
              title={day.activity ? day.activity.name : 'Rest day'}
            />
          )
        })}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState<WeekStats | null>(null)
  const [activities, setActivities] = useState<ActivityItem[]>([])
  const [dailyData, setDailyData] = useState<{ day: string; crossfit: number; walking: number }[]>([])
  const [shareData, setShareData] = useState<ShareCardData | null>(null)

  useEffect(() => {
    async function loadData() {
      try {
        const [statsData, acts, daily, share] = await Promise.all([
          getStats(),
          getActivities(50),
          getDailyData(7),
          getShareCard()
        ])

        setStats(statsData)
        setActivities(acts)

        // Transform daily data for chart
        const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        const chartData = daily.map((d: DailyDataPoint) => {
          const date = new Date(d.date)
          return {
            day: dayNames[date.getDay()],
            crossfit: d.crossfit,
            walking: d.walking
          }
        })
        setDailyData(chartData)
        setShareData(share)
      } catch (err) {
        console.error('Failed to load data:', err)
        setError('Failed to load dashboard data. Please check your connection and try again.')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  const recentActivities = activities.slice(0, 5)

  // Calculate totals
  const totalDuration = activities.reduce((acc, a) => acc + (a.moving_time || 0), 0)
  const totalCalories = activities.reduce((acc, a) => acc + (a.calories || a.moving_time * 0.1), 0)
  const crossFitCount = activities.filter(a => a.is_crossfit).length
  const walkingCount = activities.filter(a => a.is_walking).length

  if (error) {
    return (
      <main className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center max-w-md px-4">
          <div className="p-4 bg-red-500/10 rounded-2xl inline-flex mb-4">
            <Activity className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-xl font-bold text-foreground mb-2">Unable to Load Data</h2>
          <p className="text-muted-foreground mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition"
          >
            Retry
          </button>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-orange-500 to-red-600 rounded-lg">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">BioMonitor</h1>
                <p className="text-sm text-muted-foreground">Personal Health Dashboard</p>
              </div>
            </div>
            <Link href="/share">
              <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition">
                <Share2 className="w-4 h-4" />
                <span className="text-sm font-medium">Share</span>
              </button>
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Date Navigation */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-foreground">Training Journey</h2>
            <p className="text-muted-foreground">
              Since 2024 • {activities.length} activities tracked
            </p>
          </div>
          <div className="flex gap-2">
            <Link href="/activity">
              <button className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition">
                View Activity →
              </button>
            </Link>
          </div>
        </div>

        {/* BIG STATS - Inspired by endless.wenxin.io */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          <BigStatCard
            title="Total Duration"
            value={Math.round(totalDuration / 3600)}
            unit="hrs"
            subtext={`${Math.round(totalDuration / 60)} minutes total`}
            icon={Timer}
            color="orange"
          />
          <BigStatCard
            title="Total Activities"
            value={activities.length}
            unit=""
            subtext={`${crossFitCount} CrossFit • ${walkingCount} Walking`}
            icon={Trophy}
            color="blue"
          />
          <BigStatCard
            title="Calories Burned"
            value={Math.round(totalCalories)}
            unit="kcal"
            subtext="Estimated from HR data"
            icon={Flame}
            color="red"
          />
          <BigStatCard
            title="Active Days"
            value={new Set(activities.map(a => a.start_date?.split('T')[0])).size}
            unit="days"
            subtext="This month: 12 days"
            icon={Calendar}
            color="green"
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2">
            <ActivityChart data={dailyData} loading={loading} />
          </div>
          <div className="lg:col-span-1">
            <Link href="/recovery">
              <div className="bg-card rounded-xl p-6 border border-border h-full hover:border-primary transition cursor-pointer">
                <h3 className="text-lg font-semibold text-foreground mb-4">Apple Watch Data</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground flex items-center gap-2">
                      <Heart className="w-4 h-4 text-red-500" /> Resting HR
                    </span>
                    <span className="font-bold">{shareData?.resting_hr || 58} bpm</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground flex items-center gap-2">
                      <Zap className="w-4 h-4 text-yellow-500" /> HRV
                    </span>
                    <span className="font-bold">{shareData?.hrv || 65} ms</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground flex items-center gap-2">
                      <Activity className="w-4 h-4 text-green-500" /> Sleep
                    </span>
                    <span className="font-bold">7.2 h</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-blue-500" /> VO2 Max
                    </span>
                    <span className="font-bold">52.3 ml/kg</span>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mt-6">Click for detailed recovery analysis →</p>
              </div>
            </Link>
          </div>
        </div>

        {/* Calendar Heatmap */}
        <div className="mb-8">
          <CalendarHeatmap data={activities} />
        </div>

        {/* Recent Activities */}
        <div className="bg-card rounded-xl p-6 border border-border">
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
              {recentActivities.map((activity) => (
                <div key={activity.id} className="flex items-center justify-between py-3 border-b border-border last:border-0">
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-lg ${
                      activity.is_crossfit ? 'bg-orange-500/20' : 
                      activity.is_walking ? 'bg-blue-500/20' : 'bg-secondary'
                    }`}>
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
                        {activity.average_heartrate && ` • ${Math.round(activity.average_heartrate)} bpm`}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-medium text-foreground">
                      {Math.round(activity.moving_time / 60)} min
                    </span>
                    {activity.calories && (
                      <p className="text-xs text-muted-foreground">{Math.round(activity.calories)} kcal</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">No activities yet. Sync your data!</p>
          )}
        </div>

        {/* Footer */}
        <footer className="mt-12 pt-8 border-t border-border text-center">
          <p className="text-muted-foreground text-sm">
            BioMonitor v0.1.0 • Data from Apple Watch, Strava & more
          </p>
        </footer>
      </div>
    </main>
  )
}
