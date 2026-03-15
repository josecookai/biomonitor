---
skill: biomonitor
version: 1.0.0
description: Personal health dashboard aggregating fitness and wellness data from Oura Ring, WHOOP, Xiaomi Mi Band, Strava, and Apple Health into a unified FastAPI + Next.js platform with smart reminders and supplement recommendations.
author: josecookai
homepage: https://github.com/josecookai/biomonitor
tags: [health, fitness, wearables, dashboard]
requires:
  - python3
  - node
  - pip
env:
  BIOMONITOR_API_KEY: optional
  BIOMONITOR_HOST: "127.0.0.1"
  BIOMONITOR_PORT: "8000"
  NEXT_PUBLIC_API_URL: "http://localhost:8000"
  NEXT_PUBLIC_API_KEY: optional
---

# BioMonitor Skill

BioMonitor is a local-first health platform. The backend is a FastAPI server
(`api_server.py`) backed by SQLite. The frontend is a Next.js 14 app in
`dashboard/web/`. Collectors in `collectors/` pull data from each wearable.
The `engine/` layer produces smart reminders and supplement recommendations.
User profiles live in `users/data/{user_id}.yaml`.

---

## BOOTSTRAP

Step-by-step commands to get BioMonitor running from a fresh clone.

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Create config file (edit with your API tokens after copying)
cp config.example.yaml config.yaml

# 3. (Optional) Load demo data so the dashboard has something to show
python setup_demo.py

# 4. Start the backend (binds to 127.0.0.1:8000 by default)
python api_server.py &

# 5. Start the frontend
cd dashboard/web && npm install && npm run dev &

# 6. Verify backend is alive
curl http://localhost:8000/api/health
# Expected: {"status": "ok", "timestamp": "..."}

# 7. Open dashboard
# http://localhost:3000
```

Environment overrides (all optional):

```bash
export BIOMONITOR_HOST=0.0.0.0      # bind on all interfaces (set API key too!)
export BIOMONITOR_PORT=8080         # change port
export BIOMONITOR_API_KEY=secret    # enable auth — all routes except /api/health require X-API-Key header
export NEXT_PUBLIC_API_URL=http://localhost:8080
export NEXT_PUBLIC_API_KEY=secret
```

Interactive API docs are available at `http://localhost:8000/docs` when the
server is running.

---

## USERS

Three pre-configured user profiles. Profiles are YAML files in `users/data/`.

| user_id | Name  | Device        | Config key(s)                            | Profile file            |
|---------|-------|---------------|------------------------------------------|-------------------------|
| carl    | Carl  | Oura Ring     | `oura.access_token`                      | `users/data/carl.yaml`  |
| zelda   | Zelda | Xiaomi Mi Band| `xiaomi.account_email` / export JSON     | `users/data/zelda.yaml` |
| zn      | ZN    | WHOOP         | `whoop.client_id` + `whoop.client_secret`| `users/data/zn.yaml`    |

A `default` profile is also present and used as a fallback by the supplement
engine. Add arbitrary users by following OP: add_user below.

---

## OPERATIONS

### OP: sync_oura — Sync Carl's Oura Ring data

Prerequisite: `oura.access_token` set in `config.yaml`.
Token is a Personal Access Token from https://cloud.ouraring.com/personal-access-tokens

```bash
# Sync last 7 days (default)
curl -X POST "http://localhost:8000/api/oura/sync"

# Sync last 30 days
curl -X POST "http://localhost:8000/api/oura/sync?days=30"

# Verify: pull readiness scores
curl "http://localhost:8000/api/oura/readiness?days=7"

# Pull sleep data (score + duration)
curl "http://localhost:8000/api/oura/sleep?days=7"
```

Metric types written to DB: `OuraReadiness`, `OuraSleepScore`,
`OuraSleepDuration`, `OuraActivityScore`, `HeartRate`, `HeartRateVariability`.

If you get HTTP 503 the token is missing from config. If you get HTTP 401 from
Oura the token has expired — generate a new one at the URL above and update
`oura.access_token` in `config.yaml`.

---

### OP: sync_whoop — Sync ZN's WHOOP data

Prerequisite: WHOOP developer app created at https://developer.whoop.com with
redirect URI `http://localhost:8000/api/whoop/callback`.

```bash
# Step 1 — Get the authorization URL (one-time setup)
curl http://localhost:8000/api/whoop/auth-url
# → {"auth_url": "https://api.prod.whoop.com/oauth/..."}

# Step 2 — Open that URL in a browser, authorize, copy the 'code' param
#           from the redirect URL (http://localhost:8000/api/whoop/callback?code=XXXX)

# Step 3 — Exchange the code for tokens (tokens are persisted to config.yaml)
curl -X POST http://localhost:8000/api/whoop/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "XXXX"}'

# Step 4 — Sync data (tokens auto-refresh on expiry)
curl -X POST "http://localhost:8000/api/whoop/sync"
curl -X POST "http://localhost:8000/api/whoop/sync?days=14"

# Verify
curl "http://localhost:8000/api/whoop/recovery?days=7"
curl "http://localhost:8000/api/whoop/strain?days=7"
```

Metric types written to DB: `WhoopRecovery`, `WhoopStrain`, `WhoopHRV`,
`WhoopSleepScore`, `WhoopSleepDuration`, `HeartRateVariabilitySDNN`.

---

### OP: sync_strava — Sync all Strava activities

Prerequisite: `strava.access_token` (and optionally `client_id`,
`client_secret`, `refresh_token` for auto-refresh) in `config.yaml`.

```bash
# Sync last 30 days (default)
curl -X POST "http://localhost:8000/api/strava/sync"

# Sync last 90 days
curl -X POST "http://localhost:8000/api/strava/sync?days=90"

# Check connection status
curl http://localhost:8000/api/strava/stats
# → {"connected": true}

# Verify activities saved
curl "http://localhost:8000/api/activities?limit=10"
```

The collector auto-classifies activities as CrossFit (`is_crossfit=true`) or
walking (`is_walking=true`) based on activity type, name keywords, and HR.

---

### OP: send_apple_health — Push Apple Health data (Zelda)

Data arrives via the Health Auto Export iOS app posting to the webhook.
Configure the app: Automations > Add Automation > REST API >
`http://YOUR_SERVER_IP:8000/api/apple-health/webhook`.

For manual testing or scripted ingestion:

```bash
# Single heart rate record
curl -X POST http://localhost:8000/api/apple-health/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"type": "HeartRate", "date": "2026-03-15T08:00:00", "value": 62, "unit": "count/min"},
      {"type": "HeartRateVariabilitySDNN", "date": "2026-03-15T06:45:00", "value": 49, "unit": "ms"},
      {"type": "SleepAnalysis", "date": "2026-03-15T00:10:00", "value": "asleepCore", "duration_minutes": 432}
    ]
  }'

# Verify latest metrics
curl http://localhost:8000/api/health-metrics/latest

# Check metric format reference
curl http://localhost:8000/api/apple-health/formats
```

Maximum webhook payload: 5 MB. Supported metric types: `HeartRate`,
`HeartRateVariabilitySDNN`, `SleepAnalysis`, `StepCount`, `ActiveEnergyBurned`,
`OxygenSaturation`, `AppleSleepingWristTemperature`.

---

### OP: sync_xiaomi — Upload Xiaomi Mi Band data (Zelda)

Xiaomi has no live API. Export data from Mi Fitness or Gadgetbridge, then POST.

```bash
# Option A: Gadgetbridge JSON export
curl -X POST http://localhost:8000/api/xiaomi/upload \
  -H "Content-Type: application/json" \
  -d '{
    "format": "gadgetbridge",
    "data": [
      {"timestamp": 1741996800, "heart_rate": 68, "steps": 1200},
      {"timestamp": 1742000400, "heart_rate": 72, "steps": 3500}
    ]
  }'

# Option B: Mi Fitness CSV export (submit as rows of a CSV turned into JSON)
curl -X POST http://localhost:8000/api/xiaomi/upload \
  -H "Content-Type: application/json" \
  -d '{"format": "mi_fitness", "data": [{"date": "2026-03-15", "steps": 8432, "heart_rate": 70}]}'

# Option C: Real-time Gadgetbridge HTTP server plugin webhook
# Configure Gadgetbridge: Settings > HTTP server > Enable
# URL: http://YOUR_SERVER_IP:8000/api/xiaomi/webhook
curl -X POST http://localhost:8000/api/xiaomi/webhook \
  -H "Content-Type: application/json" \
  -d '{"timestamp": 1741996800, "heart_rate": 71, "steps": 4200, "battery": 85}'

# Verify
curl "http://localhost:8000/api/xiaomi/stats?days=7"
```

---

### OP: log_crossfit — Log a CrossFit workout manually

```bash
curl -X POST http://localhost:8000/api/crossfit/log \
  -H "Content-Type: application/json" \
  -d '{
    "wod_name": "Fran",
    "date": "2026-03-15T10:00:00",
    "time": "4:52",
    "rounds": 21,
    "reps": 45,
    "weight": null,
    "rpe": 8,
    "notes": "Felt strong today"
  }'

# Retrieve recent workouts
curl "http://localhost:8000/api/crossfit/workouts?limit=10"
```

All fields except `wod_name` and `date` are optional.

---

### OP: get_reminders — Get today's smart schedule

```bash
# Full merged daily timeline (recommended)
curl "http://localhost:8000/api/reminders/daily?wake_time=07:00&work_start=09:00&work_end=18:00&sleep_time=23:00"

# Individual reminder categories
curl http://localhost:8000/api/reminders/sleep
curl "http://localhost:8000/api/reminders/hydration?wake_time=07:00&sleep_time=23:00"
curl "http://localhost:8000/api/reminders/standing?work_start=09:00&work_end=18:00"
curl "http://localhost:8000/api/reminders/fitness?weekly_target=3"
curl http://localhost:8000/api/reminders/recovery
```

The daily schedule endpoint returns a list of events sorted by time, each with
`time` (HH:MM), `type` (hydration/standing/fitness/sleep/recovery), `message`,
and `priority` (high/medium/low).

The recovery endpoint scores 0-100 from WHOOP, Oura, and HRV data:
- >= 67 → green (workout)
- 34-66 → yellow (light activity)
- < 34  → red (rest)

---

### OP: get_supplements — Get supplement recommendations per user

```bash
# Daily plan grouped by timing (recommended)
curl http://localhost:8000/api/users/carl/supplements/daily-plan
curl http://localhost:8000/api/users/zelda/supplements/daily-plan
curl http://localhost:8000/api/users/zn/supplements/daily-plan

# Flat list of recommendations
curl http://localhost:8000/api/users/carl/supplements
curl http://localhost:8000/api/users/default/supplements

# All users side by side
curl http://localhost:8000/api/supplements/all-users
```

The supplement engine uses the user's profile (health_goals, sex, weight_kg,
activity_level) plus live DB metrics (avg_hrv, avg_sleep_hours, recovery_score)
to generate a personalised stack. Categories: sleep, recovery, performance,
general health, female-specific. Results are deduplicated and sorted by
priority (essential > recommended > optional).

---

### OP: add_user — Add a new user profile

Create a YAML file at `users/data/{user_id}.yaml`:

```yaml
user_id: newuser
name: Name
age: 30
weight_kg: 70.0
height_cm: 175.0
sex: male           # male / female / other
activity_level: moderate  # sedentary / light / moderate / active / very_active
device: oura        # oura / whoop / xiaomi / apple_watch / strava_only
health_goals:
  - sleep
  - recovery
  # Options: sleep, recovery, weight_loss, muscle_gain, endurance, general_health
conditions: []
  # Options: hypertension, diabetes, vegetarian, ...
# Computed fields — leave null; filled automatically from health_metrics DB
avg_sleep_hours: null
avg_hrv: null
avg_resting_hr: null
recovery_score: null
```

After creating the file the user is immediately available via the API:

```bash
curl http://localhost:8000/api/users/newuser/profile
curl http://localhost:8000/api/users/newuser/supplements/daily-plan
```

To update a profile at runtime:

```bash
curl -X PUT http://localhost:8000/api/users/newuser/profile \
  -H "Content-Type: application/json" \
  -d '{"age": 31, "weight_kg": 72.0}'
```

---

### OP: add_collector — Add a new wearable device integration

Five files need to be created or edited:

**1. Create `collectors/{name}.py`** — collector class following this pattern:

```python
from . import load_config, save_config, _REQUEST_TIMEOUT
import requests

class MyDeviceCollector:
    def __init__(self):
        config = load_config()
        self.access_token = config.get("mydevice", {}).get("access_token")

    def sync_to_database(self, db, days: int = 7) -> dict:
        if not self.access_token:
            return {"skipped": "mydevice.access_token not configured"}
        # Fetch data with timeout=(5, 30) on every requests call
        resp = requests.get(
            "https://api.mydevice.com/data",
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        count = 0
        for record in resp.json().get("data", []):
            db.save_health_metric({
                "date": record["date"],
                "metric_type": "MyMetricType",
                "value": float(record["value"]),
                "unit": "ms",
                "source": "mydevice",
            })
            count += 1
        # Always persist updated tokens
        # save_config(config)
        return {"MyMetricType": count}
```

**2. Edit `collectors/__init__.py`** — add import and export:

```python
from .mydevice import MyDeviceCollector

__all__ = [
    ...,
    "MyDeviceCollector",
]
```

**3. Edit `api_server.py`** — instantiate and add routes:

```python
from collectors import ..., MyDeviceCollector

mydevice_collector = MyDeviceCollector()

@app.post("/api/mydevice/sync")
def sync_mydevice(days: int = Field(default=7, ge=1, le=90)):
    counts = mydevice_collector.sync_to_database(db, days)
    return {"success": True, "days": days, "saved": counts}
```

**4. Update `users/data/{user}.yaml`** — set the device field:

```yaml
device: mydevice
```

**5. Create `docs/{MYDEVICE}_SETUP.md`** — document auth steps and config keys.

---

## API_REFERENCE

All endpoints return JSON. When `BIOMONITOR_API_KEY` is set, include
`-H "X-API-Key: $BIOMONITOR_API_KEY"` on every request except `/api/health`.

### Health & Status

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/health` | — | Health check (always public) |

### Activities

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/activities` | `limit` (1-200, def 30), `activity_type` (crossfit\|walking) | List activities |
| GET | `/api/daily` | `days` (1-365, def 30) | Daily aggregated CrossFit + walking data |
| GET | `/api/stats/current-week` | — | Current week CrossFit sessions + walking stats |
| GET | `/api/stats/weekly` | `weeks` (1-52, def 4) | Last N weeks aggregated stats |
| POST | `/api/activities/sync` | JSON body: Activity model | Sync a single activity from external script |

### CrossFit

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/crossfit/workouts` | `limit` (1-100, def 10) | Recent CrossFit workouts |
| POST | `/api/crossfit/log` | JSON body: CrossFitWorkout model | Log a new workout |

### Strava

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| POST | `/api/strava/sync` | `days` (1-365, def 30) | Sync last N days from Strava |
| GET | `/api/strava/stats` | — | Strava connection status |

### Apple Health

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| POST | `/api/apple-health/webhook` | JSON body: `{data: [...]}` | Receive Health Auto Export data (max 5 MB) |
| GET | `/api/health-metrics/latest` | — | Latest HR, HRV, sleep metrics |
| GET | `/api/health-metrics/history` | `days` (1-365, def 30), `metric_type` | Metric history for charts |
| GET | `/api/apple-health/formats` | — | Supported metric format reference |

### Oura Ring

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| POST | `/api/oura/sync` | `days` (1-90, def 7) | Sync Oura data for Carl |
| GET | `/api/oura/readiness` | `days` (1-90, def 7) | Readiness scores from DB |
| GET | `/api/oura/sleep` | `days` (1-90, def 7) | Sleep scores + durations from DB |

### Xiaomi Mi Band

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| POST | `/api/xiaomi/upload` | JSON body: `{format, data}` | Upload Gadgetbridge or Mi Fitness export |
| POST | `/api/xiaomi/webhook` | JSON body: XiaomiWebhookData | Real-time Gadgetbridge HTTP plugin data |
| GET | `/api/xiaomi/stats` | `days` (1-90, def 7) | Xiaomi metrics from DB |

### WHOOP

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/whoop/auth-url` | — | Get OAuth 2.0 authorization URL |
| POST | `/api/whoop/callback` | JSON body: `{"code": "..."}` | Exchange auth code for tokens |
| POST | `/api/whoop/sync` | `days` (1-90, def 7) | Sync WHOOP data for ZN |
| GET | `/api/whoop/recovery` | `days` (1-90, def 7) | Recovery scores from DB |
| GET | `/api/whoop/strain` | `days` (1-90, def 7) | Strain scores from DB |

### Reminders

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/reminders/sleep` | — | Bedtime/wake recommendation |
| GET | `/api/reminders/hydration` | `wake_time` (HH:MM), `sleep_time` (HH:MM) | Hourly water schedule |
| GET | `/api/reminders/standing` | `work_start` (HH:MM), `work_end` (HH:MM) | Stand-up reminders |
| GET | `/api/reminders/fitness` | `weekly_target` (1-7, def 3) | Workout scheduling |
| GET | `/api/reminders/recovery` | — | Recovery score 0-100 |
| GET | `/api/reminders/daily` | `wake_time`, `sleep_time`, `work_start`, `work_end` | Full merged daily timeline |

### Supplement Recommendations

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/users/{user_id}/supplements` | — | Flat supplement list for user |
| GET | `/api/users/{user_id}/supplements/daily-plan` | — | Supplements grouped by timing |
| GET | `/api/supplements/all-users` | — | All users' supplement plans side by side |

### User Profiles

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/users/{user_id}/profile` | — | Load user profile |
| PUT | `/api/users/{user_id}/profile` | JSON body: partial profile fields | Merge-update and persist profile |

### Sharing

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/share/card` | Current week stats card (CrossFit, walking, HRV, resting HR) |

---

## HEALTH_CHECKS

```bash
# 1. Backend alive
curl http://localhost:8000/api/health
# Expected: {"status": "ok", "timestamp": "..."}

# 2. Check if activity data is flowing
curl "http://localhost:8000/api/activities?limit=5"
curl http://localhost:8000/api/stats/current-week

# 3. Check health metrics (Apple Health / Oura / WHOOP)
curl http://localhost:8000/api/health-metrics/latest

# 4. Check Oura data specifically
curl "http://localhost:8000/api/oura/readiness?days=7"
curl "http://localhost:8000/api/oura/sleep?days=7"

# 5. Check WHOOP data
curl "http://localhost:8000/api/whoop/recovery?days=7"
curl "http://localhost:8000/api/whoop/strain?days=7"

# 6. Check Xiaomi data
curl "http://localhost:8000/api/xiaomi/stats?days=7"

# 7. Check all users have supplement recommendations
for user in carl zelda zn default; do
  echo "=== $user ==="
  curl -s "http://localhost:8000/api/users/$user/supplements" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"count\"]} supplements for {d[\"name\"]}')"
done

# 8. Check reminders engine
curl -s "http://localhost:8000/api/reminders/daily" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d[\"schedule\"])} reminders, recovery={d[\"recovery_score\"]}/100 ({d[\"recovery_color\"]})')"

# 9. Check Strava connection
curl http://localhost:8000/api/strava/stats
```

---

## TROUBLESHOOTING

### Backend won't start

- Run `pip install -r requirements.txt` to ensure all dependencies are present.
- Confirm port 8000 is free: `lsof -i :8000`
- Check `config.yaml` exists (copy from `config.example.yaml` if missing).
- Python 3.10+ is required.

### Oura returns HTTP 401

Token has expired or is invalid. Generate a new Personal Access Token at
https://cloud.ouraring.com/personal-access-tokens, then update `config.yaml`:

```yaml
oura:
  access_token: "eyJ..."
```

Restart the server (or the collector re-reads config on each request).

### WHOOP returns HTTP 401

Tokens are refreshed automatically on the next sync call. If the error
persists, the refresh token has also expired — re-run the full OAuth flow:

```bash
curl http://localhost:8000/api/whoop/auth-url
# Open URL, authorize, copy code
curl -X POST http://localhost:8000/api/whoop/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "NEW_CODE"}'
```

### Strava returns HTTP 401

If `client_id` + `client_secret` + `refresh_token` are configured, the
collector auto-refreshes. If not, generate a new `access_token` at
https://www.strava.com/settings/api and update `config.yaml`.

### Empty or missing metrics

Device not yet synced — run the appropriate sync OP. For Apple Health, confirm
the Health Auto Export app is configured and has sent at least one export.

### Xiaomi no data

Xiaomi has no live API. Use Gadgetbridge (free, Android) to export data:
1. Gadgetbridge > your device > Export data
2. POST the exported JSON to `/api/xiaomi/upload` with `"format": "gadgetbridge"`

For real-time data enable the Gadgetbridge HTTP server plugin pointing at
`/api/xiaomi/webhook`.

### Supplement recommendations missing for a user

Profile file does not exist. Check `users/data/{user_id}.yaml` exists and is
valid YAML. Test: `curl http://localhost:8000/api/users/{user_id}/profile`.

### API returns 403 Forbidden

`BIOMONITOR_API_KEY` is set. Add the header: `-H "X-API-Key: $BIOMONITOR_API_KEY"`.
The only public endpoint is `/api/health`.

### Port already in use

```bash
# Find the PID using port 8000
lsof -i :8000
kill <PID>
# Or use a different port
BIOMONITOR_PORT=8080 python api_server.py &
```

---

## CODING_PATTERNS

Key patterns to follow when extending the codebase.

### Collector pattern

All collectors follow the same shape. Critical rules:

```python
from . import load_config, save_config, _REQUEST_TIMEOUT

class MyCollector:
    def __init__(self):
        config = load_config()
        self.access_token = config.get("myservice", {}).get("access_token")

    def sync_to_database(self, db, days: int = 7) -> dict:
        # Always use the shared timeout tuple on every requests call
        resp = requests.get(url, headers=..., timeout=_REQUEST_TIMEOUT)
        # _REQUEST_TIMEOUT = (5, 30)  — 5s connect, 30s read

        # Always call save_config() after refreshing tokens
        config = load_config()
        config["myservice"]["access_token"] = new_token
        save_config(config)
```

### Saving a metric to the database

```python
db.save_health_metric({
    "date": "2026-03-15T08:00:00",   # ISO string or date string
    "metric_type": "HeartRate",       # string key, e.g. OuraReadiness, WhoopRecovery
    "value": 62.0,                    # numeric
    "unit": "bpm",                    # string
    "source": "oura",                 # collector name
})
```

### Querying metrics from the database

```python
# Returns a list of dicts: [{date, metric_type, value, unit, source}, ...]
records = db.get_health_metrics_history(days=30, metric_type="HeartRateVariabilitySDNN")

# Latest snapshot of all metric types
snapshot = db.get_latest_health_metrics()
```

### Auth middleware

When `BIOMONITOR_API_KEY` is set in the environment, the middleware in
`api_server.py` enforces `X-API-Key` on all routes except those in
`_PUBLIC_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc"}`.

No decorator needed on individual routes — protection is automatic.

### User profiles (immutable updates)

```python
from users import load_profile, save_profile
from dataclasses import replace

profile = load_profile("carl")            # Returns UserProfile dataclass or None
updated = replace(profile, weight_kg=82.0)  # Immutable copy with changes
save_profile(updated)                     # Persists to users/data/carl.yaml
```

### Supplement engine integration

```python
from engine.supplements import SupplementEngine

engine = SupplementEngine()
supplements = engine.recommend(profile, health_metrics_dict)
plan = engine.as_daily_plan(supplements)
# plan keys: morning, pre_workout, post_workout, evening, with_meal,
#            total_supplements, estimated_monthly_cost_usd
```

### Timing values for supplements

Valid `timing` strings: `"morning"`, `"pre_workout"`, `"post_workout"`,
`"evening"`, `"with_meal"`. Unknown values fall back to `"morning"` in
`as_daily_plan`.

### Evidence and priority levels

- `evidence_level`: `"strong"` | `"moderate"` | `"emerging"`
- `priority`: `"essential"` | `"recommended"` | `"optional"`

### File size and function length guidelines

- Keep files under 800 lines; 200-400 lines is typical.
- Keep functions under 50 lines.
- New collectors go in their own file in `collectors/`.
- New engine modules go in `engine/`.

### Config structure

```yaml
strava:
  client_id: "..."
  client_secret: "..."
  access_token: "..."
  refresh_token: "..."

apple_health:
  export_path: "/tmp/apple_health_exports"
  webhook_enabled: true

oura:
  access_token: "..."

whoop:
  client_id: "..."
  client_secret: "..."
  access_token: "..."
  refresh_token: "..."
  redirect_uri: "http://localhost:8000/api/whoop/callback"

xiaomi:
  account_email: "..."
  password: "..."
```

All values are optional. Features are silently disabled when credentials are
absent — collectors return `{"skipped": "...reason..."}` rather than raising.
