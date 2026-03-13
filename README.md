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
                    │   FastAPI Backend   │  ← api_server.py
                    │   Port: 8000        │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │   SQLite Database   │
                    └─────────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │   Next.js Dashboard │  ← dashboard/web
                    │   Port: 3000        │
                    └─────────────────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Python dependencies
pip install fastapi uvicorn pandas sqlalchemy

# Dashboard dependencies
cd dashboard/web
npm install
```

### 2. Start the Backend API

```bash
# From project root
python api_server.py

# API will be available at http://localhost:8000
# API docs: http://localhost:8000/docs
```

### 3. Start the Dashboard (in another terminal)

```bash
cd dashboard/web
npm run dev

# Dashboard will be available at http://localhost:3000
```

### 4. Sync Your Data

```bash
# Sync from Strava (configure your token first)
python main.py sync --source strava

# Or log a CrossFit workout manually
python main.py log --wod "Fran" --time "4:52" --rpe 8
```

## 📊 Dashboard Pages

| Page | URL | Description |
|------|-----|-------------|
| **Overview** | `/` | Weekly summary, key metrics, recent activities |
| **Activity** | `/activity` | CrossFit & Walking detailed analysis |
| **Recovery** | `/recovery` | Heart rate, HRV, and sleep tracking |
| **Share** | `/share` | Generate and export shareable summaries |

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/activities` | GET | List activities (with filters) |
| `/api/stats/current-week` | GET | Current week statistics |
| `/api/stats/weekly` | GET | Weekly aggregated stats |
| `/api/daily` | GET | Daily data for charts |
| `/api/crossfit/workouts` | GET | List CrossFit workouts |
| `/api/crossfit/log` | POST | Log a CrossFit workout |
| `/api/share/card` | GET | Get data for share card |

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

## 🗂️ Project Structure

```
biomonitor/
├── api_server.py           # FastAPI backend
├── main.py                 # CLI entry point
├── SKILL.md               # OpenClaw skill manifest
├── config.yaml            # Configuration (not in git)
├── collectors/            # Data collection modules
├── processors/            # Data analysis
├── storage/               # Database layer
├── dashboard/
│   └── web/               # Next.js frontend
│       ├── app/           # Pages
│       ├── lib/api.ts     # API client
│       └── ...
└── biomonitor.db          # SQLite database
```

## 📈 Features

### Phase 1: MVP ✅
- [x] Strava data sync
- [x] SQLite storage
- [x] Dashboard with Next.js
- [x] Real-time metrics
- [x] Shareable cards

### Phase 2: Automation (In Progress)
- [ ] Apple Health auto-sync
- [ ] CrossFit auto-detection
- [ ] Playwright screenshot generation
- [ ] Vercel deployment

### Phase 3: Social
- [ ] Multi-user support
- [ ] Family & friend groups
- [ ] Challenges and rankings

## 📄 License

MIT
