# BioMonitor

BioMonitor is a personal health dashboard that aggregates your fitness and wellness data from multiple sources in one beautiful interface. Track CrossFit workouts, Apple Watch metrics, and Strava activities with integrated analytics and shareable reports.

## Features

- **Multi-Source Data Integration** — Strava API, Apple Health via Health Auto Export webhook, manual CrossFit logging
- **Real-time Metrics** — Heart rate, HRV, sleep quality, walking distance, training load
- **CrossFit Tracking** — WOD logging, performance trends, PRs, RPE tracking
- **Activity Calendar** — Visual heatmap of training activity
- **Weekly Reports** — Automated summaries with stats and recovery data
- **Shareable Cards** — Generate and export weekly summary images
- **Optional API Authentication** — Secure with `BIOMONITOR_API_KEY` env var

## Architecture

```
Data Sources (Strava, Apple Health, Manual)
           ↓
   FastAPI Backend (Python)
           ↓
   SQLite Database
           ↓
   Next.js Dashboard (React/TypeScript)
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Strava API credentials (optional, for workout sync)

### 1. Backend Setup

```bash
# Clone repository
git clone https://github.com/josecookai/biomonitor.git
cd biomonitor

# Install Python dependencies
pip install fastapi uvicorn pandas sqlalchemy pyyaml requests

# Load demo data (optional, for testing)
python3 setup_demo.py

# Start the API server
python api_server.py
```

The API will be available at `http://localhost:8000` with auto-generated docs at `http://localhost:8000/docs`.

### 2. Frontend Setup

```bash
cd dashboard/web
npm install
npm run dev
```

The dashboard will be available at `http://localhost:3000`.

### 3. (Optional) Configure Strava Sync

Create `config.yaml` in the project root:

```yaml
strava:
  client_id: "your_strava_client_id"
  client_secret: "your_strava_client_secret"
  access_token: "your_strava_access_token"
  refresh_token: "your_strava_refresh_token"

apple_health:
  export_path: "/tmp/apple_health_exports"
```

Then sync data:

```bash
curl -X POST "http://localhost:8000/api/strava/sync?days=30"
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BIOMONITOR_API_KEY` | (unset) | Optional API key for authentication. If unset, API is public. |
| `BIOMONITOR_HOST` | `127.0.0.1` | Server bind address |
| `BIOMONITOR_PORT` | `8000` | Server port |

Example:

```bash
export BIOMONITOR_API_KEY="your-secret-key"
export BIOMONITOR_HOST="0.0.0.0"
export BIOMONITOR_PORT="8000"
python api_server.py
```

When `BIOMONITOR_API_KEY` is set, all requests (except `/api/health` and `/docs`) must include the header:

```
X-API-Key: your-secret-key
```

## API Reference

All endpoints return JSON. When `BIOMONITOR_API_KEY` is configured, include `X-API-Key` header on all requests except those listed as "Public".

### Health & Status

| Endpoint | Method | Public | Description |
|----------|--------|--------|-------------|
| `/api/health` | GET | Yes | Health check, returns `{"status": "ok"}` |

### Activities

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/activities?limit=30&activity_type=crossfit\|walking` | GET | List activities, optionally filtered by type |
| `/api/daily?days=30` | GET | Daily aggregated data (CrossFit count, walking distance) |
| `/api/stats/current-week` | GET | Current week statistics (sessions, distance, time) |
| `/api/stats/weekly?weeks=4` | GET | Last N weeks of aggregated stats |

### CrossFit Workouts

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/crossfit/workouts?limit=10` | GET | Recent CrossFit workouts |
| `/api/crossfit/log` | POST | Log a new CrossFit workout |

**Request body for POST `/api/crossfit/log`:**

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

### Strava Integration

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/strava/sync?days=30` | POST | Sync activities from Strava (last N days) |
| `/api/strava/stats` | GET | Strava connection status |

### Apple Health Integration

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/apple-health/webhook` | POST | Receive Health Auto Export data |
| `/api/health-metrics/latest` | GET | Latest health metrics (HR, HRV, sleep) |
| `/api/health-metrics/history?days=30&metric_type=HeartRateVariability` | GET | Health metrics history |

### Share & Reports

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/share/card` | GET | Generate data for weekly summary card |

## Data Sources Setup

### Strava

1. Create a Strava application: https://www.strava.com/settings/api
2. Authorize your app to access your account
3. Copy `Client ID`, `Client Secret`, `Access Token`, and `Refresh Token` to `config.yaml`
4. Sync activities via API or CLI:

```bash
curl -X POST "http://localhost:8000/api/strava/sync?days=30" \
  -H "X-API-Key: your-key"
```

### Apple Health (Health Auto Export)

Health Auto Export is a third-party iOS app that exports Apple Health data via webhook.

1. Install **Health Auto Export** from [App Store](https://apps.apple.com/app/health-auto-export/id1115567069)
2. Open the app and configure the webhook:
   - **URL:** `http://your-domain:8000/api/apple-health/webhook`
   - **Method:** POST
3. Select data types to export (Heart Rate, HRV, Sleep, etc.)
4. Enable automatic periodic push or push manually
5. Data will be saved to the database automatically

Example webhook request (from Health Auto Export):

```bash
curl -X POST "http://localhost:8000/api/apple-health/webhook" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "data": [
      {
        "type": "HKQuantityTypeIdentifierHeartRateVariability",
        "value": 45.2,
        "unit": "ms",
        "date": "2026-03-15T10:00:00Z"
      }
    ]
  }'
```

## Self-Hosting

### Basic Deployment (Linux/Docker)

```bash
# Ensure Python 3.10+ is installed
python3 --version

# Install dependencies
pip install -r requirements.txt

# Start backend (production)
BIOMONITOR_API_KEY="your-secret-key" \
BIOMONITOR_HOST="0.0.0.0" \
BIOMONITOR_PORT="8000" \
python api_server.py
```

### Docker Setup

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "api_server.py"]
```

Build and run:

```bash
docker build -t biomonitor .
docker run -p 8000:8000 \
  -e BIOMONITOR_API_KEY="your-key" \
  -e BIOMONITOR_HOST="0.0.0.0" \
  -v /data/biomonitor.db:/app/biomonitor.db \
  biomonitor
```

### Systemd Service

Create `/etc/systemd/system/biomonitor.service`:

```ini
[Unit]
Description=BioMonitor API Server
After=network.target

[Service]
Type=simple
User=biomonitor
WorkingDirectory=/home/biomonitor/app
EnvironmentFile=/home/biomonitor/.env
ExecStart=/usr/bin/python3 /home/biomonitor/app/api_server.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable biomonitor
sudo systemctl start biomonitor
sudo systemctl status biomonitor
```

## Project Structure

```
biomonitor/
├── api_server.py              # FastAPI application
├── main.py                    # CLI interface
├── setup_demo.py              # Demo data generator
├── config.yaml                # Config (not in git)
├── biomonitor.db              # SQLite database
│
├── collectors/                # Data collection
│   ├── __init__.py           # Strava, Apple Health collectors
│
├── processors/                # Data analysis
│   └── __init__.py           # Metrics calculator
│
├── storage/                   # Database layer
│   └── __init__.py           # BioDatabase class
│
├── docs/                      # Documentation
│   ├── APPLE_WATCH_DATA.md
│   └── HARDWARE_ROADMAP.md
│
├── dashboard/
│   └── web/                   # Next.js frontend
│       ├── app/               # Pages
│       ├── lib/               # API client
│       └── package.json
│
└── README.md
```

## Troubleshooting

**API not responding:**
- Check if API is running: `curl http://localhost:8000/api/health`
- Verify port 8000 is not in use: `lsof -i :8000`
- Check logs for errors

**Strava sync returns 401:**
- Access token has expired
- Refresh token in `config.yaml` is invalid
- Re-authorize the app at https://www.strava.com/settings/api

**No data showing in dashboard:**
- Run `python3 setup_demo.py` to load sample data
- Check `/api/activities` endpoint to verify data exists
- Ensure frontend can reach API at `http://localhost:8000`

**Apple Health webhook not receiving data:**
- Verify webhook URL is correct in Health Auto Export app
- Check API logs for incoming requests
- Ensure `X-API-Key` header is set if authentication is enabled
- Verify Health Auto Export app has permission to read health data

## Configuration Reference

### `config.yaml`

```yaml
strava:
  client_id: "your_client_id"
  client_secret: "your_client_secret"
  access_token: "your_access_token"
  refresh_token: "your_refresh_token"

apple_health:
  export_path: "/tmp/apple_health_exports"
  webhook_enabled: true

oura:
  access_token: YOUR_OURA_PERSONAL_ACCESS_TOKEN
```

All values are optional. If not set, features are disabled.

## Development

### CLI Commands

```bash
# Sync Strava data
python main.py sync --source strava --days 30

# Log CrossFit workout
python main.py log --wod "Fran" --time "4:52" --rpe 8

# Generate weekly report
python main.py report

# Check configuration
python main.py config

# Strava status
python main.py strava status
```

### Database Schema

- `activities` — Strava activities with metadata
- `crossfit_workouts` — Manually logged CrossFit sessions
- `health_metrics` — Apple Health data (HR, HRV, sleep)
- `daily_summaries` — Aggregated daily stats
- `settings` — App configuration

## License

MIT License — see LICENSE file for details

## Acknowledgments

- UI design inspired by [Endless Miles](https://endless.wenxin.io/)
- Built with FastAPI, Next.js, SQLite, and React
- Integrations: Strava API, Apple Health Auto Export
