'use client'

import { 
  Activity, 
  Heart, 
  Footprints, 
  Timer,
  TrendingUp,
  Flame,
  Moon,
  Share2,
  Dumbbell
} from 'lucide-react'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  AreaChart,
  Area
} from 'recharts'

// Mock data - replace with API calls
const weeklyData = [
  { day: 'Mon', crossfit: 1, walking: 3.2, hr: 72 },
  { day: 'Tue', crossfit: 0, walking: 5.1, hr: 68 },
  { day: 'Wed', crossfit: 1, walking: 2.8, hr: 75 },
  { day: 'Thu', crossfit: 0, walking: 4.5, hr: 70 },
  { day: 'Fri', crossfit: 1, walking: 3.0, hr: 73 },
  { day: 'Sat', crossfit: 0, walking: 6.2, hr: 65 },
  { day: 'Sun', crossfit: 0, walking: 4.0, hr: 68 },
]

const hrvData = [
  { date: 'W1', hrv: 45 },
  { date: 'W2', hrv: 48 },
  { date: 'W3', hrv: 52 },
  { date: 'W4', hrv: 49 },
]

function MetricCard({ 
  title, 
  value, 
  unit, 
  icon: Icon, 
  trend, 
  trendUp 
}: { 
  title: string
  value: string | number
  unit?: string
  icon: any
  trend?: string
  trendUp?: boolean 
}) {
  return (
    <div className="bg-card rounded-xl p-6 border border-border">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-muted-foreground text-sm">{title}</p>
          <div className="flex items-baseline gap-1 mt-2">
            <span className="text-3xl font-bold text-foreground">{value}</span>
            {unit && <span className="text-muted-foreground text-sm">{unit}</span>}
          </div>
          {trend && (
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

function ActivityChart() {
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
        <BarChart data={weeklyData}>
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

function HRVChart() {
  return (
    <div className="bg-card rounded-xl p-6 border border-border">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-foreground">Heart Rate Variability</h3>
        <p className="text-muted-foreground text-sm">Weekly average HRV (ms)</p>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={hrvData}>
          <defs>
            <linearGradient id="hrvGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} />
          <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} domain={[30, 70]} />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'hsl(var(--card))', 
              border: '1px solid hsl(var(--border))',
              borderRadius: '8px'
            }}
          />
          <Area 
            type="monotone" 
            dataKey="hrv" 
            stroke="#10b981" 
            fillOpacity={1} 
            fill="url(#hrvGradient)" 
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function Dashboard() {
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
            <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition">
              <Share2 className="w-4 h-4" />
              <span className="text-sm font-medium">Share</span>
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Date Navigation */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-foreground">This Week</h2>
            <p className="text-muted-foreground">March 10 - March 16, 2026</p>
          </div>
          <div className="flex gap-2">
            <button className="px-3 py-1 text-sm bg-secondary rounded-md hover:bg-secondary/80 transition">
              ← Prev
            </button>
            <button className="px-3 py-1 text-sm bg-secondary rounded-md hover:bg-secondary/80 transition">
              Next →
            </button>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <MetricCard
            title="CrossFit Sessions"
            value={3}
            unit="/ week"
            icon={Dumbbell}
            trend="On target"
            trendUp={true}
          />
          <MetricCard
            title="Walking Distance"
            value={28.8}
            unit="km"
            icon={Footprints}
            trend="+12% vs last week"
            trendUp={true}
          />
          <MetricCard
            title="Avg Resting HR"
            value={70}
            unit="bpm"
            icon={Heart}
            trend="Normal range"
            trendUp={true}
          />
          <MetricCard
            title="Training Load"
            value={485}
            unit="TRIMP"
            icon={Flame}
            trend="High this week"
            trendUp={false}
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2">
            <ActivityChart />
          </div>
          <div className="lg:col-span-1">
            <HRVChart />
          </div>
        </div>

        {/* Recent Activities */}
        <div className="bg-card rounded-xl p-6 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4">Recent Activities</h3>
          <div className="space-y-4">
            {[
              { name: 'Murph', type: 'CrossFit', time: '45:32', date: 'Today', icon: Dumbbell },
              { name: 'Morning Walk', type: 'Walking', time: '45 min', date: 'Today', icon: Footprints },
              { name: 'Fran', type: 'CrossFit', time: '4:52', date: 'Yesterday', icon: Dumbbell },
              { name: 'Evening Stroll', type: 'Walking', time: '30 min', date: 'Yesterday', icon: Footprints },
            ].map((activity, i) => (
              <div key={i} className="flex items-center justify-between py-3 border-b border-border last:border-0">
                <div className="flex items-center gap-4">
                  <div className="p-2 bg-secondary rounded-lg">
                    <activity.icon className="w-4 h-4 text-foreground" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">{activity.name}</p>
                    <p className="text-sm text-muted-foreground">{activity.type} • {activity.date}</p>
                  </div>
                </div>
                <span className="text-sm font-medium text-foreground">{activity.time}</span>
              </div>
            ))}
          </div>
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
