'use client'

import { useState, useRef } from 'react'
import { Share2, Download, ArrowLeft, Check } from 'lucide-react'
import Link from 'next/link'
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

const weeklyData = [
  { day: 'Mon', crossfit: 1, walking: 3.2, hrv: 45 },
  { day: 'Tue', crossfit: 0, walking: 5.1, hrv: 48 },
  { day: 'Wed', crossfit: 1, walking: 2.8, hrv: 52 },
  { day: 'Thu', crossfit: 0, walking: 4.5, hrv: 49 },
  { day: 'Fri', crossfit: 1, walking: 3.0, hrv: 51 },
  { day: 'Sat', crossfit: 0, walking: 6.2, hrv: 53 },
  { day: 'Sun', crossfit: 0, walking: 4.0, hrv: 50 },
]

export default function SharePage() {
  const [copied, setCopied] = useState(false)
  const shareCardRef = useRef<HTMLDivElement>(null)

  const handleCopy = () => {
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-4">
            <Link href="/" className="p-2 hover:bg-secondary rounded-lg transition">
              <ArrowLeft className="w-5 h-5 text-muted-foreground" />
            </Link>
            <div>
              <h1 className="text-xl font-bold text-foreground">Share Your Progress</h1>
              <p className="text-sm text-muted-foreground">Generate shareable summaries</p>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Share Card Preview */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-4">Preview</h3>
            <div 
              ref={shareCardRef}
              className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-8 text-white"
              style={{ aspectRatio: '1/1' }}
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-gradient-to-br from-orange-500 to-red-600 rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold text-sm">B</span>
                  </div>
                  <span className="font-semibold">BioMonitor</span>
                </div>
                <span className="text-slate-400 text-sm">Mar 10-16, 2026</span>
              </div>

              {/* Title */}
              <h2 className="text-2xl font-bold mb-6">Week in Review</h2>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-white/10 rounded-xl p-4">
                  <p className="text-slate-400 text-xs mb-1">CrossFit</p>
                  <p className="text-3xl font-bold">3<span className="text-lg text-slate-400">/3</span></p>
                  <p className="text-green-400 text-xs mt-1">On target 🎯</p>
                </div>
                <div className="bg-white/10 rounded-xl p-4">
                  <p className="text-slate-400 text-xs mb-1">Walking</p>
                  <p className="text-3xl font-bold">28.8</p>
                  <p className="text-slate-400 text-xs mt-1">kilometers</p>
                </div>
                <div className="bg-white/10 rounded-xl p-4">
                  <p className="text-slate-400 text-xs mb-1">Avg HRV</p>
                  <p className="text-3xl font-bold">49</p>
                  <p className="text-green-400 text-xs mt-1">ms ↑</p>
                </div>
                <div className="bg-white/10 rounded-xl p-4">
                  <p className="text-slate-400 text-xs mb-1">Resting HR</p>
                  <p className="text-3xl font-bold">70</p>
                  <p className="text-slate-400 text-xs mt-1">bpm</p>
                </div>
              </div>

              {/* Mini Chart */}
              <div className="bg-white/5 rounded-xl p-4">
                <p className="text-slate-400 text-xs mb-2">Activity Overview</p>
                <ResponsiveContainer width="100%" height={100}>
                  <BarChart data={weeklyData}>
                    <Bar dataKey="crossfit" fill="#f97316" radius={[2, 2, 0, 0]} />
                    <Bar dataKey="walking" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Footer */}
              <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between">
                <span className="text-slate-400 text-xs">biomonitor.app</span>
                <span className="text-slate-500 text-xs">#CrossFit #Health</span>
              </div>
            </div>
          </div>

          {/* Export Options */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-4">Export Options</h3>
            
            <div className="space-y-4">
              <button 
                onClick={handleCopy}
                className="w-full flex items-center justify-between p-4 bg-card border border-border rounded-xl hover:border-primary transition"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-secondary rounded-lg">
                    {copied ? <Check className="w-5 h-5 text-green-500" /> : <Share2 className="w-5 h-5" />}
                  </div>
                  <div className="text-left">
                    <p className="font-medium text-foreground">Copy as Image</p>
                    <p className="text-sm text-muted-foreground">PNG format, high quality</p>
                  </div>
                </div>
                {copied && <span className="text-sm text-green-500">Copied!</span>}
              </button>

              <button className="w-full flex items-center justify-between p-4 bg-card border border-border rounded-xl hover:border-primary transition">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-secondary rounded-lg">
                    <Download className="w-5 h-5" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium text-foreground">Download Report</p>
                    <p className="text-sm text-muted-foreground">PDF weekly summary</p>
                  </div>
                </div>
              </button>

              <button className="w-full flex items-center justify-between p-4 bg-card border border-border rounded-xl hover:border-primary transition">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-secondary rounded-lg">
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                  </div>
                  <div className="text-left">
                    <p className="font-medium text-foreground">Share to X/Twitter</p>
                    <p className="text-sm text-muted-foreground">Post with auto-generated text</p>
                  </div>
                </div>
              </button>

              <button className="w-full flex items-center justify-between p-4 bg-card border border-border rounded-xl hover:border-primary transition">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-secondary rounded-lg">
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.12.03-1.99 1.27-5.62 3.72-.53.36-1.01.54-1.44.53-.47-.01-1.38-.27-2.05-.49-.83-.27-1.49-.42-1.43-.88.03-.25.38-.51 1.05-.78 4.11-1.79 6.85-2.98 8.24-3.57 3.92-1.64 4.73-1.93 5.26-1.93.12 0 .37.03.54.18.14.12.18.28.2.45-.01.07-.01.24-.02.38z"/>
                    </svg>
                  </div>
                  <div className="text-left">
                    <p className="font-medium text-foreground">Share to Telegram</p>
                    <p className="text-sm text-muted-foreground">Send to friends or groups</p>
                  </div>
                </div>
              </button>
            </div>

            {/* Templates */}
            <div className="mt-8">
              <h3 className="text-sm font-medium text-muted-foreground mb-4">Templates</h3>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 border border-primary rounded-lg cursor-pointer">
                  <p className="text-sm font-medium text-foreground">Weekly Summary</p>
                  <p className="text-xs text-muted-foreground">Current</p>
                </div>
                <div className="p-3 border border-border rounded-lg cursor-pointer hover:border-primary transition">
                  <p className="text-sm font-medium text-foreground">Monthly Review</p>
                  <p className="text-xs text-muted-foreground">30-day trends</p>
                </div>
                <div className="p-3 border border-border rounded-lg cursor-pointer hover:border-primary transition">
                  <p className="text-sm font-medium text-foreground">Goal Progress</p>
                  <p className="text-xs text-muted-foreground">vs targets</p>
                </div>
                <div className="p-3 border border-border rounded-lg cursor-pointer hover:border-primary transition">
                  <p className="text-sm font-medium text-foreground">PR Highlights</p>
                  <p className="text-xs text-muted-foreground">Personal records</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
