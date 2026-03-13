# BioMonitor

Personal health metrics tracking skill for OpenClaw. Monitor your CrossFit, walking, and Apple Watch data in one dashboard.

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Apple Watch   │     │    Strava API   │     │  Manual Input   │
│   (HealthKit)   │     │  (Activity)     │     │  (CrossFit)     │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────┐
                    │   Data Collector    │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │   Data Processor    │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │   Dashboard/API     │
                    └─────────────────────┘
```

## 📊 Features

- **Activity Tracking**: CrossFit (3x/week) + Walking
- **Recovery Metrics**: HRV, Sleep, Resting HR from Apple Watch
- **Dashboard**: Real-time metrics and trends
- **Shareable**: Generate screenshot reports
- **Multi-User**: Family & friends support (Phase 2)

## 🚀 Quick Start

```bash
# Install
skill install biomonitor

# Configure
skill config biomonitor
# - Strava API credentials
# - Apple Health export path
# - Dashboard preferences

# Run
biomonitor sync
biomonitor dashboard
```

## 📁 Structure

```
biomonitor/
├── collectors/          # Data collection modules
│   ├── apple_health.py
│   ├── strava_sync.py
│   └── crossfit_logger.py
├── processors/          # Data analysis
│   ├── metrics_calculator.py
│   └── trend_analyzer.py
├── storage/            # Database layer
│   └── database.py
├── dashboard/          # Web dashboard
│   └── web/
├── sharing/            # Screenshot generation
│   └── poster_generator.py
└── reports/            # Automated reports
    └── weekly_summary.py
```

## 🔌 Data Sources

1. **Apple Watch** (HealthKit): Heart rate, HRV, Sleep, Activity
2. **Strava API**: Workouts, GPS, Segment data
3. **Manual Input**: CrossFit WODs, RPE scores

## 📈 Dashboard Features

- Weekly CrossFit sessions count
- Walking distance/time trends
- Recovery metrics (HRV, sleep quality)
- Training load distribution
- Shareable weekly summary cards

## 🔮 Roadmap

- [x] Phase 1: MVP with Strava + basic dashboard
- [ ] Phase 2: Apple Health auto-sync, multi-user
- [ ] Phase 3: Social features, challenges, friends

## 📄 License

MIT
