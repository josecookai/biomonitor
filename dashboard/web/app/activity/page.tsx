'use client'

import { useEffect, useState } from 'react'
import { Dumbbell, Footprints, ArrowLeft, Loader2 } from 'lucide-react'
import Link from 'next/link'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line
} from 'recharts'
import { getWeeklyStats, type WeeklyStatEntry } from '@/lib/api'

interface CrossfitChartEntry {
  week: string
  sessions: number
}

interface WalkingChartEntry {
  week: string
  distance: number
  time: number
}

export default function ActivityPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [crossfitHistory, setCrossfitHistory] = useState<CrossfitChartEntry[]>([])
  const [walkingHistory, setWalkingHistory] = useState<WalkingChartEntry[]>([])

  useEffect(() => {
    async function loadData() {
      try {
        const weeklyStats: WeeklyStatEntry[] = await getWeeklyStats(8)

        setCrossfitHistory(
          weeklyStats.map((entry) => ({
            week: entry.week,
            sessions: entry.crossfit_sessions
          }))
        )

        setWalkingHistory(
          weeklyStats.map((entry) => ({
            week: entry.week,
            distance: entry.walking_distance_km,
            time: entry.walking_time_min
          }))
        )
      } catch (err) {
        console.error('Failed to load weekly stats:', err)
        setError('Failed to load activity data. Please check your connection and try again.')
      } finally {
        setLoading(false)
      }
    }

    loadData()
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
              <h1 className="text-xl font-bold text-foreground">Activity Analysis</h1>
              <p className="text-sm text-muted-foreground">Detailed workout breakdown</p>
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
            {/* CrossFit Section */}
            <div className="mb-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-orange-500/20 rounded-lg">
                  <Dumbbell className="w-5 h-5 text-orange-500" />
                </div>
                <h2 className="text-xl font-bold text-foreground">CrossFit Performance</h2>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-card rounded-xl p-6 border border-border">
                  <h3 className="text-sm font-medium text-muted-foreground mb-4">Weekly Sessions</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={crossfitHistory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="week" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }} />
                      <Bar dataKey="sessions" fill="#f97316" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="bg-card rounded-xl p-6 border border-border">
                  <h3 className="text-sm font-medium text-muted-foreground mb-4">Sessions Trend</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={crossfitHistory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="week" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }} />
                      <Line type="monotone" dataKey="sessions" stroke="#f97316" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Walking Section */}
            <div className="mb-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <Footprints className="w-5 h-5 text-blue-500" />
                </div>
                <h2 className="text-xl font-bold text-foreground">Walking Analysis</h2>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-card rounded-xl p-6 border border-border">
                  <h3 className="text-sm font-medium text-muted-foreground mb-4">Weekly Distance (km)</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={walkingHistory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="week" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }} />
                      <Bar dataKey="distance" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="bg-card rounded-xl p-6 border border-border">
                  <h3 className="text-sm font-medium text-muted-foreground mb-4">Weekly Time (min)</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={walkingHistory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="week" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }} />
                      <Line type="monotone" dataKey="time" stroke="#3b82f6" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  )
}
