'use client'

import { useEffect, useState } from 'react'
import { 
  Activity, 
  Heart, 
  Footprints, 
  Dumbbell,
  Flame,
  Share2,
  Loader2
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
  Area
} from 'recharts'
import Link from 'next/link'
import { getActivities, getCurrentWeekStats, getDailyData, getShareCard } from '@/lib/api'

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

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<any>(null)
  const [activities, setActivities] = useState<any[]>([])
  const [dailyData, setDailyData] = useState<any[]>([])
  const [shareData, setShareData] = useState<any>(null)

  useEffect(() => {
    async function loadData() {
      try {
        const [statsData, acts, daily, share] = await Promise.all([
          getCurrentWeekStats(),
          getActivities(10),
          getDailyData(7),
          getShareCard()
        ])
        
        setStats(statsData)
        setActivities(acts)
        
        // Transform daily data for chart
        const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        const chartData = daily.map((d: any) => {
          const date = new Date(d.date)
          return {
            day: dayNames[date.getDay()],
            crossfit: d.crossfit,
            walking: d.walking
          }
        })
        setDailyData(chartData)
        setShareData(share)
      } catch (error) {
        console.error('Failed to load data:', error)
      } finally {
        setLoading(false)
      }
    }
    
    loadData()
  }, [])

  const recentActivities = activities.slice(0, 4)

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
            <h2 className="text-2xl font-bold text-foreground">This Week</h2>
            <p className="text-muted-foreground">
              {stats?.week_start || new Date().toLocaleDateString()}
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

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <MetricCard
            title="CrossFit Sessions"
            value={stats?.crossfit_sessions || 0}
            unit="/ week"
            icon={Dumbbell}
            trend={stats?.crossfit_sessions >= 3 ? "On target 🎯" : `${3 - stats?.crossfit_sessions} to go`}
            trendUp={stats?.crossfit_sessions >= 3}
            loading={loading}
          />
          <MetricCard
            title="Walking Distance"
            value={stats?.walking_distance_km?.toFixed(1) || 0}
            unit="km"
            icon={Footprints}
            trend="This week"
            trendUp={true}
            loading={loading}
          />
          <MetricCard
            title="Avg Resting HR"
            value={shareData?.resting_hr || 70}
            unit="bpm"
            icon={Heart}
            trend="Normal range"
            trendUp={true}
            loading={loading}
          />
          <MetricCard
            title="Training Load"
            value={Math.round((stats?.walking_time_min || 0) * 1.5)}
            unit="TRIMP"
            icon={Flame}
            trend="Calculated"
            trendUp={true}
            loading={loading}
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
                <h3 className="text-lg font-semibold text-foreground mb-4">Recovery</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">HRV</span>
                    <span className="font-bold">{shareData?.hrv || 49} ms</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Resting HR</span>
                    <span className="font-bold">{shareData?.resting_hr || 70} bpm</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Sleep</span>
                    <span className="font-bold">7.2 h</span>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mt-6">Click for details →</p>
              </div>
            </Link>
          </div>
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
              {recentActivities.map((activity, i) => (
                <div key={i} className="flex items-center justify-between py-3 border-b border-border last:border-0">
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
                      </p>
                    </div>
                  </div>
                  <span className="text-sm font-medium text-foreground">
                    {Math.round(activity.moving_time / 60)} min
                  </span>
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
            BioMonitor v0.1.0 • Data from Apple Watch & Strava
          </p>
        </footer>
      </div>
    </main>
  )
}
