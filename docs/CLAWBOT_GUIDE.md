# BioMonitor Operations Guide for AI Agents

This guide is optimized for autonomous execution by AI agents (clawbot, Claude, etc.). All instructions assume the working directory is `/home/ubuntu/biomonitor` and the development environment is set up.

## Quick Reference

**API Base URL:** `http://localhost:8000`
**Dashboard URL:** `http://localhost:3000`
**API Docs:** `http://localhost:8000/docs`
**Database:** `biomonitor.db` (SQLite)

---

## Task: Start Backend Server

### Prerequisites
- Python 3.10+
- Dependencies installed: `pip install fastapi uvicorn pandas sqlalchemy pyyaml requests`

### Steps

1. Navigate to project root:
```bash
cd /home/ubuntu/biomonitor
```

2. Start the API server:
```bash
python api_server.py
```

3. Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

4. Verify health:
```bash
curl http://localhost:8000/api/health
```

**Expected response:**
```json
{"status":"ok","timestamp":"2026-03-15T..."}
```

### Environment Variables
- `BIOMONITOR_HOST` — Bind address (default: `127.0.0.1`)
- `BIOMONITOR_PORT` — Port number (default: `8000`)
- `BIOMONITOR_API_KEY` — Optional authentication key

### Success Criteria
- Server responds to `http://localhost:8000/api/health` with status 200
- API documentation available at `http://localhost:8000/docs`

---

## Task: Start Frontend Dashboard

### Prerequisites
- Node.js 18+
- npm dependencies installed

### Steps

1. Navigate to frontend directory:
```bash
cd /home/ubuntu/biomonitor/dashboard/web
```

2. Install dependencies (if needed):
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

4. Expected output:
```
> next dev
  ▲ Next.js 14.2.0
  - Local:        http://localhost:3000
  - Environments: .env.local

 ✓ Ready in 1.23s
```

5. Verify dashboard is accessible:
```bash
curl http://localhost:3000 | head -20
```

### Port Configuration
- Frontend runs on `http://localhost:3000`
- API calls to `http://localhost:8000` (hardcoded in `lib/api.ts`)

### Success Criteria
- Dashboard loads at `http://localhost:3000`
- No console errors about API connectivity
- Activity data visible (if database has records)

---

## Task: Load Demo Data

### Steps

1. Navigate to project root:
```bash
cd /home/ubuntu/biomonitor
```

2. Run demo setup:
```bash
python3 setup_demo.py
```

3. Expected output:
```
✓ Demo data loaded
- 2 CrossFit workouts
- 7.5 km of walking
- Sample health metrics
```

4. Verify data was loaded:
```bash
curl http://localhost:8000/api/activities?limit=5
```

### What Gets Created
- Database: `biomonitor.db`
- 2 CrossFit workouts (Fran, Grace)
- 3 walking activities
- Sample health metrics

### Success Criteria
- `biomonitor.db` file exists and is > 100KB
- `/api/activities` returns non-empty list
- Dashboard homepage shows data

---

## Task: Sync Data from Strava

### Prerequisites
- Backend running on `http://localhost:8000`
- `config.yaml` file with Strava credentials

### Configuration File

Create `/home/ubuntu/biomonitor/config.yaml`:

```yaml
strava:
  client_id: "YOUR_CLIENT_ID"
  client_secret: "YOUR_CLIENT_SECRET"
  access_token: "YOUR_ACCESS_TOKEN"
  refresh_token: "YOUR_REFRESH_TOKEN"
```

### Steps

1. Verify Strava is configured:
```bash
curl -s http://localhost:8000/api/strava/stats | jq .
```

**Expected response if connected:**
```json
{"connected": true}
```

**Expected response if not configured:**
```json
{"connected": false}
```

2. Sync last 30 days of activities:
```bash
curl -X POST "http://localhost:8000/api/strava/sync?days=30"
```

3. With API key authentication:
```bash
curl -X POST "http://localhost:8000/api/strava/sync?days=30" \
  -H "X-API-Key: your-secret-key"
```

4. Expected response:
```json
{
  "success": true,
  "synced_activities": 12,
  "days": 30
}
```

### Troubleshooting: 401 Unauthorized

If you get a 401 error:
1. Access token has expired
2. Update refresh tokens in `config.yaml`
3. Retry the sync

```bash
# Check API logs for details
curl -X POST http://localhost:8000/api/strava/sync?days=30 -v
```

### Success Criteria
- Sync returns `"success": true`
- `synced_activities` count > 0
- New activities visible in `/api/activities`

---

## Task: Log a CrossFit Workout

### Endpoint

```
POST /api/crossfit/log
```

### Required Parameters

```json
{
  "wod_name": "Fran",
  "date": "2026-03-15T10:30:00"
}
```

### Optional Parameters

```json
{
  "wod_name": "Fran",
  "date": "2026-03-15T10:30:00",
  "time": "4:52",
  "rounds": 21,
  "reps": 45,
  "weight": 65.0,
  "rpe": 8,
  "notes": "Felt strong today"
}
```

### Examples

1. Minimal logging:
```bash
curl -X POST "http://localhost:8000/api/crossfit/log" \
  -H "Content-Type: application/json" \
  -d '{
    "wod_name": "Murph",
    "date": "2026-03-15T09:00:00"
  }'
```

2. Complete workout log:
```bash
curl -X POST "http://localhost:8000/api/crossfit/log" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{
    "wod_name": "Fran",
    "date": "2026-03-15T10:30:00",
    "time": "4:52",
    "rounds": 21,
    "reps": 45,
    "weight": 65.0,
    "rpe": 8,
    "notes": "New PR!"
  }'
```

3. With shell variable for current time:
```bash
DATETIME=$(date -u +"%Y-%m-%dT%H:%M:%S")
curl -X POST "http://localhost:8000/api/crossfit/log" \
  -H "Content-Type: application/json" \
  -d "{
    \"wod_name\": \"Grace\",
    \"date\": \"$DATETIME\",
    \"time\": \"3:15\",
    \"rounds\": 30,
    \"rpe\": 7
  }"
```

### Expected Response

```json
{
  "success": true,
  "workout_id": 42
}
```

### Success Criteria
- Returns status 200
- Response contains `"success": true`
- `workout_id` is a positive integer
- Workout appears in `/api/crossfit/workouts`

---

## Task: Check Health Metrics

### Get Latest Health Metrics

```bash
curl "http://localhost:8000/api/health-metrics/latest"
```

**Expected response:**
```json
{
  "resting_hr": 58,
  "hrv": 45.2,
  "sleep_hours": 7.5,
  "timestamp": "2026-03-15T08:00:00"
}
```

### Get Health Metrics History

1. Last 30 days of all metrics:
```bash
curl "http://localhost:8000/api/health-metrics/history?days=30"
```

2. Specific metric type (HRV):
```bash
curl "http://localhost:8000/api/health-metrics/history?days=30&metric_type=HeartRateVariability"
```

3. With API key:
```bash
curl "http://localhost:8000/api/health-metrics/history?days=30" \
  -H "X-API-Key: your-secret-key"
```

### Expected Response Format

```json
[
  {
    "date": "2026-03-15",
    "metric_type": "HeartRateVariability",
    "value": 45.2,
    "unit": "ms"
  },
  {
    "date": "2026-03-14",
    "metric_type": "HeartRateVariability",
    "value": 42.8,
    "unit": "ms"
  }
]
```

### Success Criteria
- Returns status 200
- Response is valid JSON array
- Each record has `date`, `metric_type`, `value`, `unit`

---

## Task: Send Apple Health Data (Webhook)

### Webhook URL

```
POST /api/apple-health/webhook
```

### Prerequisites

- Backend running
- Health Auto Export app configured (or manual webhook)
- API key set (optional but recommended)

### Manual Webhook Test

1. Send sample Apple Health data:
```bash
curl -X POST "http://localhost:8000/api/apple-health/webhook" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{
    "data": [
      {
        "type": "HKQuantityTypeIdentifierHeartRateVariability",
        "value": 48.5,
        "unit": "ms",
        "date": "2026-03-15T08:00:00Z"
      },
      {
        "type": "HKQuantityTypeIdentifierRestingHeartRate",
        "value": 56,
        "unit": "count/min",
        "date": "2026-03-15T08:00:00Z"
      },
      {
        "type": "HKQuantityTypeIdentifierSleepDuration",
        "value": 7.5,
        "unit": "hour",
        "date": "2026-03-15T08:00:00Z"
      }
    ],
    "metadata": {
      "source": "Health Auto Export",
      "timestamp": "2026-03-15T08:30:00Z"
    }
  }'
```

2. Expected response:
```json
{
  "success": true,
  "records_processed": 3,
  "metrics_types": ["HKQuantityTypeIdentifierHeartRateVariability", ...]
}
```

### Configure in Health Auto Export App

1. Install app from App Store
2. Go to Settings > Webhooks
3. Set webhook URL: `http://YOUR_DOMAIN:8000/api/apple-health/webhook`
4. If API key is set:
   - Add header: `X-API-Key: your-secret-key`
5. Select data types: Heart Rate, HRV, Sleep, etc.
6. Enable automatic sync or push manually

### Success Criteria
- Webhook returns status 200
- `"success": true` in response
- `records_processed` > 0
- Data appears in `/api/health-metrics/latest`

---

## Task: Retrieve Activity Data

### List All Activities

```bash
curl "http://localhost:8000/api/activities?limit=30"
```

### Filter by Type

1. CrossFit only:
```bash
curl "http://localhost:8000/api/activities?activity_type=crossfit&limit=30"
```

2. Walking only:
```bash
curl "http://localhost:8000/api/activities?activity_type=walking&limit=30"
```

3. Custom limit:
```bash
curl "http://localhost:8000/api/activities?limit=100"
```

### Expected Response

```json
[
  {
    "id": 1,
    "name": "Fran",
    "type": "Workout",
    "start_date": "2026-03-15T10:30:00",
    "distance": null,
    "moving_time": 292,
    "average_heartrate": 165.4,
    "max_heartrate": 185,
    "is_crossfit": true,
    "is_walking": false
  },
  {
    "id": 2,
    "name": "Morning Walk",
    "type": "Walk",
    "start_date": "2026-03-15T08:00:00",
    "distance": 2500.0,
    "moving_time": 1800,
    "average_heartrate": 95.2,
    "max_heartrate": 120,
    "is_crossfit": false,
    "is_walking": true
  }
]
```

### Success Criteria
- Returns status 200
- Response is valid JSON array
- Each activity has required fields

---

## Task: Get Weekly Statistics

### Current Week

```bash
curl "http://localhost:8000/api/stats/current-week"
```

**Expected response:**
```json
{
  "week_start": "2026-03-09",
  "crossfit_sessions": 3,
  "walking_distance_km": 12.5,
  "walking_time_min": 750,
  "total_activities": 8
}
```

### Last N Weeks

```bash
curl "http://localhost:8000/api/stats/weekly?weeks=4"
```

**Expected response:**
```json
[
  {
    "week": "2026-W10",
    "crossfit_sessions": 3,
    "walking_distance_km": 12.5,
    "walking_time_min": 750,
    "total_activities": 8
  },
  {
    "week": "2026-W09",
    "crossfit_sessions": 2,
    "walking_distance_km": 9.8,
    "walking_time_min": 590,
    "total_activities": 6
  }
]
```

### Success Criteria
- Returns status 200
- Stats include `crossfit_sessions`, `walking_distance_km`, `walking_time_min`
- `week_start` or `week` is properly formatted

---

## Task: Get Daily Data

### Last 30 Days

```bash
curl "http://localhost:8000/api/daily?days=30"
```

### Custom Period

```bash
curl "http://localhost:8000/api/daily?days=60"
```

### Expected Response

```json
[
  {
    "date": "2026-03-15",
    "crossfit": 1,
    "walking": 3.5
  },
  {
    "date": "2026-03-14",
    "crossfit": 0,
    "walking": 5.2
  },
  {
    "date": "2026-03-13",
    "crossfit": 1,
    "walking": 2.1
  }
]
```

### Success Criteria
- Returns status 200
- Each day has `date`, `crossfit` (count), `walking` (km)
- Dates are in YYYY-MM-DD format

---

## Task: Get Shareable Card Data

Generates weekly summary card data for sharing.

```bash
curl "http://localhost:8000/api/share/card"
```

### Expected Response

```json
{
  "week": "2026-03-09",
  "crossfit": {
    "completed": 3,
    "target": 3
  },
  "walking": {
    "distance_km": 12.5
  },
  "hrv": 45.2,
  "resting_hr": 58
}
```

### Success Criteria
- Returns status 200
- Includes week, CrossFit stats, walking distance, HRV, resting HR

---

## Troubleshooting

### Backend Won't Start

**Symptom:** `Address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process (replace PID with actual number)
kill -9 <PID>

# Or use different port
BIOMONITOR_PORT=8001 python api_server.py
```

### Strava Sync Returns 401

**Symptom:**
```json
{"detail": "Sync failed: 401 Unauthorized"}
```

**Solution:**
1. Check tokens in `config.yaml` are correct
2. Re-authorize at https://www.strava.com/settings/api
3. Update `access_token` and `refresh_token`
4. Retry sync

### API Key Authentication Fails

**Symptom:**
```json
{"detail": "Forbidden"}
```

**Solution:**
1. Verify `BIOMONITOR_API_KEY` env var is set:
```bash
echo $BIOMONITOR_API_KEY
```

2. Include header in request:
```bash
curl -H "X-API-Key: your-secret-key" http://localhost:8000/api/activities
```

3. Verify header value matches env var exactly

### Dashboard Can't Connect to API

**Symptom:** "Failed to load activities" or blank dashboard

**Solution:**
1. Verify backend is running:
```bash
curl http://localhost:8000/api/health
```

2. Check frontend logs in browser console
3. Verify API URL is `http://localhost:8000` (not `localhost:8000`)
4. Check CORS headers in API response

### No Data in Dashboard

**Symptom:** Empty activities list

**Solution:**
1. Load demo data:
```bash
python3 setup_demo.py
```

2. Or manually log a workout:
```bash
curl -X POST "http://localhost:8000/api/crossfit/log" \
  -H "Content-Type: application/json" \
  -d '{"wod_name":"Test","date":"2026-03-15T10:00:00"}'
```

3. Check database directly:
```bash
sqlite3 biomonitor.db "SELECT COUNT(*) FROM activities;"
```

### Apple Health Webhook Not Working

**Symptom:** Webhook returns 500 error or data not saved

**Solution:**
1. Verify backend is running
2. Test webhook manually:
```bash
curl -X POST "http://localhost:8000/api/apple-health/webhook" \
  -H "Content-Type: application/json" \
  -d '{"data":[{"type":"test","value":42,"unit":"unit","date":"2026-03-15T08:00:00Z"}]}'
```

3. Check API logs for errors
4. Verify Health Auto Export URL is correct:
   - Should be `http://YOUR_DOMAIN:8000/api/apple-health/webhook`
   - Port must match `BIOMONITOR_PORT`

---

## Common Workflows

### Complete Setup Flow

1. Start backend:
```bash
cd /home/ubuntu/biomonitor && python api_server.py
```

2. Start frontend (in another terminal):
```bash
cd /home/ubuntu/biomonitor/dashboard/web && npm run dev
```

3. Load demo data:
```bash
python3 /home/ubuntu/biomonitor/setup_demo.py
```

4. Open dashboard:
```
http://localhost:3000
```

### Daily Strava Sync

```bash
curl -X POST "http://localhost:8000/api/strava/sync?days=1" \
  -H "X-API-Key: your-secret-key"
```

### Log Workout and Check Stats

```bash
# Log workout
curl -X POST "http://localhost:8000/api/crossfit/log" \
  -H "Content-Type: application/json" \
  -d '{"wod_name":"Fran","date":"'$(date -u +%Y-%m-%dT%H:%M:%S)'","time":"4:52","rpe":8}'

# View stats
curl "http://localhost:8000/api/stats/current-week"
```

### Export Weekly Summary

```bash
curl "http://localhost:8000/api/share/card" \
  -H "X-API-Key: your-secret-key" | jq .
```

---

**Last Updated:** 2026-03-15
**For API Reference:** See `http://localhost:8000/docs` (Swagger UI)
