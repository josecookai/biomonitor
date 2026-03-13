'use client'

import { Dumbbell, Footprints, ArrowLeft } from 'lucide-react'
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

const crossfitHistory = [
  { week: 'W1', sessions: 3, avgTime: 35 },
  { week: 'W2', sessions: 2, avgTime: 40 },
  { week: 'W3', sessions: 3, avgTime: 38 },
  { week: 'W4', sessions: 3, avgTime: 32 },
]

const walkingHistory = [
  { week: 'W1', distance: 25, time: 180 },
  { week: 'W2', distance: 22, time: 160 },
  { week: 'W3', distance: 28, time: 200 },
  { week: 'W4', distance: 28.8, time: 210 },
]

export default function ActivityPage() {
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
              <h3 className="text-sm font-medium text-muted-foreground mb-4">Avg Workout Time (min)</h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={crossfitHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="week" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }} />
                  <Line type="monotone" dataKey="avgTime" stroke="#f97316" strokeWidth={2} />
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
      </div>
    </main>
  )
}
