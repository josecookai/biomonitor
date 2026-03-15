# BioMonitor

*Personal health dashboard that aggregates fitness and wellness data from multiple wearables and sources.*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.100+-00a651.svg)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/next.js-14+-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

BioMonitor is an open-source personal health platform that syncs data from Strava, Apple Health, Oura Ring, WHOOP, and Xiaomi Mi Band into a unified dashboard. Track workouts, heart rate variability, sleep patterns, and get intelligent recommendations tailored to your goals.

## Dashboard

> 📸 *Dashboard screenshot — connect your device and sync to see your data*

Real-time activity heatmap, weekly health metrics, personalized supplement recommendations, and smart reminders for sleep, hydration, and recovery.

## Features

### 📊 Data Sources
- **Strava** — Running, cycling, swimming workouts with detailed metrics
- **Apple Health** — Heart rate, HRV, sleep via Health Auto Export webhook
- **Oura Ring** — Sleep score, readiness, temperature trends
- **WHOOP** — Recovery score, strain, HRV measurements
- **Xiaomi Mi Band** — Steps, heart rate, sleep tracking

### 🏋️ Activity Tracking
- CrossFit workout logging with RPE, rounds, and performance notes
- Walking distance and step aggregation
- Multi-source activity merging and deduplication
- Training load and recovery metrics

### 💤 Health Metrics
- Heart rate variability (HRV) trends
- Sleep quality and duration analysis
- Resting heart rate baselines
- Recovery score and readiness assessment

### 🔔 Smart Reminders
- Personalized sleep time and wake recommendations
- Hydration reminders based on activity
- Standing break suggestions
- Fitness session scheduling

### 💊 Supplement Recommendations
- Profile-based supplement stacks
- Evidence-level filtering (strong, moderate, emerging)
- Cost estimates and contraindication checks
- Real-time adjustments based on health metrics

### 👥 Multi-User Support
- Carl — Oura Ring user, endurance focus
- Zelda — Xiaomi Mi Band user, general fitness
- ZN — WHOOP user, recovery tracking

### 🔒 Security & Privacy
- Optional API key authentication
- Local-first data storage (SQLite)
- No cloud sync by default
- Webhook payload validation and rate limiting

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Clone & Install Backend

```bash
git clone https://github.com/josecookai/biomonitor
cd biomonitor
pip install -r requirements.txt
cp config.example.yaml config.yaml
# Edit config.yaml with your API tokens (optional)
python api_server.py
```

The API runs at `http://localhost:8000`. View interactive docs at `http://localhost:8000/docs`.

### 2. Install Frontend

```bash
cd dashboard/web
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

### 3. (Optional) Load Demo Data

```bash
python setup_demo.py
```

## Architecture

```
┌────────────────────────────────────────────────┐
│            BioMonitor Stack                    │
├────────────────┬────────────────────────────────┤
│  Frontend      │ Next.js 14 + TypeScript        │
│  Backend       │ FastAPI + SQLite               │
│  Collectors    │ Strava · Oura · WHOOP ·        │
│                │ Apple Health · Xiaomi          │
│  Engine        │ Reminders · Supplements        │
└────────────────┴────────────────────────────────┘
```

## Device Setup

| Device | Primary User | Setup Guide | Auth Method |
|--------|--------------|-------------|-------------|
| Strava | Any | — | OAuth 2.0 |
| Apple Health | Any (Zelda) | [↓ Apple Watch](#-zelda--apple-watch--apple-health) | Webhook |
| Oura Ring | Carl | [↓ Oura Ring](#-carl--oura-ring) · [docs/OURA_SETUP.md](docs/OURA_SETUP.md) | Personal Access Token |
| Xiaomi Mi Band | Zelda | [docs/XIAOMI_SETUP.md](docs/XIAOMI_SETUP.md) | Export via Gadgetbridge |
| WHOOP | ZN | [↓ WHOOP](#-zn--whoop) · [docs/WHOOP_SETUP.md](docs/WHOOP_SETUP.md) | OAuth 2.0 |

---

## 🔑 API Key Setup — Step by Step

### 🟠 Carl — Oura Ring

Oura uses a **Personal Access Token** — no OAuth, no app registration needed.

**Step 1 — Log in to Oura Cloud**

Go to **https://cloud.ouraring.com** and sign in with your Oura account.

**Step 2 — Open Personal Access Tokens**

> Profile (top right) → **Personal Access Tokens** → **Create New Token**

Or go directly: **https://cloud.ouraring.com/personal-access-tokens**

**Step 3 — Create a token**

- Name: `BioMonitor`
- Click **Create**
- ⚠️ Copy the token immediately — it is shown **only once**

**Step 4 — Add to config.yaml**

```yaml
oura:
  access_token: "eyJ..."   # paste your token here
```

**Step 5 — Sync**

```bash
curl -X POST http://localhost:8000/api/oura/sync
```

✅ Done. Carl's sleep, readiness, and HRV data will appear in the dashboard.

---

### 🟣 Zelda — Apple Watch / Apple Health

Apple Health does not have a direct API — data is pushed via the **Health Auto Export** iOS app (free).

**Step 1 — Install Health Auto Export on iPhone**

Search "Health Auto Export" on the App Store, or go to:
> **https://apps.apple.com/app/health-auto-export-json-csv/id1115567069**

**Step 2 — Configure automatic export**

In the app:
1. Tap **Automations** → **Add Automation**
2. Select metrics: Heart Rate, HRV, Sleep Analysis, Step Count, Active Energy
3. Set **Export Format** to `JSON`
4. Set **Destination** to `REST API`
5. Enter URL: `http://YOUR_SERVER_IP:8000/api/apple-health/webhook`
6. Set interval: every **15 minutes** or **1 hour**

> 💡 If your server is on a Mac at home, use your local IP (e.g. `192.168.1.x`). For remote servers, use your public IP or domain.

**Step 3 — Send a test export**

In the app, tap **Export Now** and check the server responds `200 OK`.

**Step 4 — Verify data**

```bash
curl http://localhost:8000/api/health-metrics/latest
```

✅ Done. Zelda's heart rate, sleep, and HRV will update automatically.

---

### 🔵 ZN — WHOOP

WHOOP uses **OAuth 2.0** — requires a free developer account.

**Step 1 — Create a WHOOP Developer account**

Go to **https://developer.whoop.com** and sign in with your WHOOP credentials.

**Step 2 — Create a new application**

> **My Apps** → **Create App**

Fill in:
- **App Name**: `BioMonitor`
- **Redirect URI**: `http://localhost:8000/api/whoop/callback`
- **Scopes**: check all of — `read:recovery` `read:sleep` `read:workout` `read:cycles` `read:body_measurement`

Click **Save**. Copy your **Client ID** and **Client Secret**.

**Step 3 — Add credentials to config.yaml**

```yaml
whoop:
  client_id: "abc123"
  client_secret: "xyz789"
  redirect_uri: "http://localhost:8000/api/whoop/callback"
```

**Step 4 — Authorize BioMonitor**

```bash
# Get the authorization URL
curl http://localhost:8000/api/whoop/auth-url
# → {"auth_url": "https://api.prod.whoop.com/oauth/..."}
```

Open that URL in your browser → log in with WHOOP → click **Authorize**.

You'll be redirected to `localhost:8000/api/whoop/callback?code=XXXX` — the server exchanges the code automatically.

**Step 5 — Sync**

```bash
curl -X POST http://localhost:8000/api/whoop/sync
```

✅ Done. ZN's recovery score, HRV, strain, and sleep data will appear in the dashboard.

---

## API Reference

All endpoints return JSON. Optional API key authentication via `X-API-Key` header.

### Activities
| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/activities?limit=30&activity_type=crossfit\|walking` | GET | List activities, optionally filtered |
| `GET /api/daily?days=30` | GET | Daily aggregated stats |
| `GET /api/stats/current-week` | GET | Current week statistics |
| `GET /api/stats/weekly?weeks=4` | GET | Last N weeks of aggregated stats |

### CrossFit
| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/crossfit/workouts?limit=10` | GET | Recent CrossFit workouts |
| `POST /api/crossfit/log` | POST | Log a new workout |

**POST `/api/crossfit/log` request body:**
```json
{
  "wod_name": "Fran",
  "date": "2026-03-15T10:30:00",
  "time": "4:52",
  "rounds": 21,
  "reps": 45,
  "weight": null,
  "rpe": 8,
  "notes": "Felt strong today"
}
```

### Strava
| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /api/strava/sync?days=30` | POST | Sync last N days of activities |
| `GET /api/strava/stats` | GET | Strava connection status |

### Apple Health
| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /api/apple-health/webhook` | POST | Receive Health Auto Export data |
| `GET /api/health-metrics/latest` | GET | Latest HR, HRV, sleep metrics |
| `GET /api/health-metrics/history?days=30&metric_type=HeartRateVariability` | GET | Metric history |

### Health & Status
| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/health` | GET | Health check (public) |

## Configuration

Create `config.yaml` in the project root with your API credentials:

```yaml
strava:
  client_id: "your_strava_client_id"
  client_secret: "your_strava_client_secret"
  access_token: "your_strava_access_token"
  refresh_token: "your_strava_refresh_token"

apple_health:
  export_path: "/tmp/apple_health_exports"
  webhook_enabled: true

oura:
  access_token: "your_oura_personal_access_token"

whoop:
  client_id: "your_whoop_client_id"
  client_secret: "your_whoop_client_secret"
  access_token: "your_whoop_access_token"
  refresh_token: "your_whoop_refresh_token"

xiaomi:
  account_email: "your_xiaomi_account_email"
  password: "your_xiaomi_password"  # or export JSON file instead
```

All values are optional. Features are disabled if not configured.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BIOMONITOR_API_KEY` | (unset) | Optional API key. If set, all requests except `/api/health` require `X-API-Key` header |
| `BIOMONITOR_HOST` | `127.0.0.1` | Server bind address |
| `BIOMONITOR_PORT` | `8000` | Server port |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend API URL |
| `NEXT_PUBLIC_API_KEY` | (unset) | Frontend API key (optional) |

## Project Structure

```
biomonitor/
├── api_server.py              # FastAPI application
├── main.py                    # CLI interface
├── config.yaml                # Configuration (not in git)
├── biomonitor.db              # SQLite database
│
├── collectors/                # Device integrations
│   ├── __init__.py           # Strava, Apple Health, Oura, WHOOP, Xiaomi
│   ├── oura.py
│   ├── whoop.py
│   └── xiaomi.py
│
├── engine/                    # Intelligence layer
│   ├── reminders.py          # Sleep, hydration, standing reminders
│   └── supplements.py        # Personalized supplement recommendations
│
├── storage/                   # Database layer
│   └── __init__.py           # BioDatabase class
│
├── processors/                # Metrics calculation
│   └── __init__.py           # MetricsCalculator
│
├── users/                     # User profiles
│   └── data/
│       ├── carl.md           # Oura Ring user
│       ├── zelda.md          # Xiaomi user
│       └── zn.md             # WHOOP user
│
├── dashboard/web/             # Next.js frontend
│   ├── app/                  # Pages and layouts
│   ├── lib/                  # API client
│   └── package.json
│
└── docs/                      # Setup guides
    ├── OURA_SETUP.md
    ├── XIAOMI_SETUP.md
    └── WHOOP_SETUP.md
```

## Contributing

We welcome contributions! Here's how you can help:

- **Report bugs** — Open an issue with steps to reproduce
- **Request features** — Discuss new integrations and features via GitHub issues
- **Submit PRs** — Fork, create a feature branch, and send a pull request

Please follow the existing code style and include tests for new functionality.

## License

MIT License — See [LICENSE](LICENSE) for details.
