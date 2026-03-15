# BioMonitor

Personal health metrics tracking skill for OpenClaw. Monitor your CrossFit, walking, and Apple Watch data in one beautiful dashboard.

> 🎨 **UI Design Inspiration**: [Endless Miles](https://endless.wenxin.io/) - Clean, minimal, data-focused

## ✨ Features

- 📊 **Training Journey Overview** - Total duration, activities, calories (inspired by Endless Miles)
- 🏋️ **CrossFit Tracking** - WOD logging, PR records, time trends
- 🍎 **Apple Watch Integration** - Heart rate, HRV, sleep, recovery data
- 📅 **Activity Calendar** - GitHub-style heatmap of your training
- 📤 **Shareable Reports** - Generate beautiful summary cards
- 🔌 **Multi-Platform** - Strava, Apple Health, and more coming soon

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Data Sources                                   │
├──────────────┬──────────────┬──────────────┬──────────────┬──────────┤
│ Apple Watch  │    Strava    │   Garmin     │   Concept2   │  Manual  │
│  (HealthKit) │     API      │  (Planned)   │  (Planned)   │   Input  │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┴────┬─────┘
       └───────────────┴───────────────┴──────────────┴────────────┘
                                 │
                                 ▼
                    ┌─────────────────────┐
                    │   FastAPI Backend   │  ← api_server.py
                    │   Port: 8000        │      (Python)
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   SQLite Database   │  ← biomonitor.db
                    │   (biomonitor.db)   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Next.js Dashboard │  ← dashboard/web
                    │   Port: 3000        │      (React/TS)
                    └─────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) Strava API credentials

### 1. Clone & Setup

```bash
git clone https://github.com/josecookai/biomonitor.git
cd biomonitor

# Load demo data
python3 setup_demo.py
```

### 2. Install Dependencies

```bash
# Python backend
pip install fastapi uvicorn pandas sqlalchemy

# Frontend
cd dashboard/web
npm install
```

### 3. Start the Servers

Terminal 1 - Backend:
```bash
python api_server.py
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

Terminal 2 - Frontend:
```bash
cd dashboard/web
npm run dev
# Dashboard: http://localhost:3000
```

### 4. Sync Your Data

```bash
# Strava sync (configure token first)
python main.py sync --source strava

# Manual CrossFit logging
python main.py log --wod "Fran" --time "4:52" --rpe 8
```

---

## 📊 Dashboard Pages

| Page | URL | Description |
|------|-----|-------------|
| **Home** | `/` | Training journey overview with big stats |
| **Activity** | `/activity` | Detailed CrossFit & walking analysis |
| **Recovery** | `/recovery` | Apple Watch data: HR, HRV, sleep |
| **Share** | `/share` | Generate and export summary cards |

---

## 🍎 Apple Watch Integration

### Supported Data
- ✅ **Activity**: Workouts, calories, distance
- ✅ **Heart Rate**: Resting HR, HRV, zones
- ✅ **Sleep**: Duration, stages, efficiency
- ✅ **Recovery**: Training readiness, temperature

### Setup
1. Install [Health Auto Export](https://apps.apple.com/app/health-auto-export/id1115567069) on iPhone
2. Configure Webhook: `http://your-server:8000/api/apple-health/webhook`
3. Select data types to sync
4. Enable automatic push

📖 **Full Guide**: [docs/APPLE_WATCH_DATA.md](docs/APPLE_WATCH_DATA.md)

---

## 🔌 Hardware Integration Roadmap

### ✅ Supported Now
- Apple Watch (Series 3+)
- Strava

### 🚧 In Development
- **Garmin**: Fenix, Epix, Forerunner series
- **Concept2 PM5**: RowErg, SkiErg, BikeErg (Hyrox support!)

### 📋 Planned
- **Xiaomi**: Mi Band 9, Watch S3/S4
- **Oura Ring**: Sleep & recovery scores
- **WHOOP 4.0**: Strain & recovery tracking

🏆 **Hyrox Special**: Concept2 integration for 8x1km + 8 workstation race analysis

📖 **Full Roadmap**: [docs/HARDWARE_ROADMAP.md](docs/HARDWARE_ROADMAP.md)

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/activities` | GET | List activities (with filters) |
| `/api/stats` | GET | All-time statistics |
| `/api/daily` | GET | Daily aggregated data |
| `/api/crossfit/workouts` | GET | List CrossFit workouts |
| `/api/crossfit/log` | POST | Log a CrossFit workout |
| `/api/apple-health/webhook` | POST | Receive Apple Health data |
| `/api/share/card` | GET | Get share card data |

---

## ⚙️ Configuration

Create `config.yaml` in the project root:

```yaml
strava:
  client_id: "your_client_id"
  client_secret: "your_client_secret"
  access_token: "your_access_token"
  refresh_token: "your_refresh_token"

dashboard:
  port: 3000
  host: "localhost"
```

---

## 🗂️ Project Structure

```
biomonitor/
├── api_server.py              # FastAPI backend
├── main.py                    # CLI entry point
├── setup_demo.py              # One-click demo data
├── SKILL.md                   # OpenClaw skill manifest
├── DEMO_GUIDE.md              # Presentation guide
├── config.yaml                # Configuration (not in git)
├── collectors/                # Data collection modules
│   ├── apple_health.py        # Apple Watch collector
│   ├── strava.py              # Strava collector
│   └── concept2.py            # Concept2 collector (WIP)
├── processors/                # Data analysis
├── storage/                   # Database layer
├── docs/                      # Documentation
│   ├── APPLE_WATCH_DATA.md    # Apple Watch data formats
│   └── HARDWARE_ROADMAP.md    # Hardware integration plan
└── dashboard/
    └── web/                   # Next.js frontend
        ├── app/               # Pages
        │   ├── page.tsx       # Main dashboard
        │   ├── activity/      # Activity details
        │   └── recovery/      # Recovery metrics
        └── lib/api.ts         # API client
```

---

## 📈 Development Roadmap

### Phase 1: MVP ✅
- [x] Strava data sync
- [x] CrossFit workout logging
- [x] Dashboard with Next.js
- [x] Real-time metrics
- [x] Shareable cards
- [x] Demo data setup

### Phase 2: Automation 🚧
- [ ] Apple Health auto-sync (Webhook)
- [ ] CrossFit auto-detection from HR data
- [ ] Playwright screenshot generation
- [ ] Vercel deployment ready

### Phase 3: Multi-Platform 🔌
- [ ] Garmin Connect integration
- [ ] Concept2 PM5 support (Hyrox!)
- [ ] Xiaomi / Mi Band support
- [ ] Oura Ring integration
- [ ] WHOOP 4.0 integration

### Phase 4: Social 👥
- [ ] Multi-user support
- [ ] Family & friend groups
- [ ] Challenges and rankings
- [ ] Public profile pages

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Adding New Hardware Support

1. Create a new collector in `collectors/`
2. Implement the `BaseCollector` interface
3. Add data mapping to unified schema
4. Update [HARDWARE_ROADMAP.md](docs/HARDWARE_ROADMAP.md)
5. Submit a PR!

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- UI inspiration from [Endless Miles](https://endless.wenxin.io/)
- Built for the OpenClaw ecosystem
- Made with ❤️ for CrossFit athletes and health enthusiasts
