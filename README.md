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

## 🚂 Railway Deploy

BioMonitor is deployed on Railway as two services:

- **Web**: [https://biomonitor-web-production.up.railway.app](https://biomonitor-web-production.up.railway.app)
- **API**: [https://biomonitor-api-production.up.railway.app](https://biomonitor-api-production.up.railway.app)

Deployment model:

- `biomonitor-api`: FastAPI backend from repo root
- `biomonitor-web`: static Next.js export from `dashboard/web`

Required Railway variables:

- `biomonitor-web`: `NEXT_PUBLIC_API_URL=https://biomonitor-api-production.up.railway.app`
- `biomonitor-api`: `CORS_ORIGINS=https://biomonitor-web-production.up.railway.app`
- `biomonitor-api`: `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_ACCESS_TOKEN`, `STRAVA_REFRESH_TOKEN`

Detailed setup:
[docs/RAILWAY_DEPLOY.md](/Users/bowenwang/Documents/Openclaw%20Skill/biomonitor/docs/RAILWAY_DEPLOY.md)

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
