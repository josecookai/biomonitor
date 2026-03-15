---
name: biomonitor
description: Personal health dashboard integrating Strava, Oura, WHOOP, Apple Health, Xiaomi Mi Band. Manage multi-user health data, sync devices, get smart reminders and supplement recommendations.
trigger: biomonitor, health dashboard, sync strava, oura ring, whoop, health metrics, supplement recommendations, sleep reminders
---

# BioMonitor Skill

## Project Overview

BioMonitor is an open-source personal health platform that aggregates fitness and wellness data from five wearable sources into a unified local-first dashboard. The stack is:

- **Backend**: FastAPI (Python 3.10+) serving a REST API at `http://localhost:8000`
- **Database**: SQLite via `BioDatabase` in `storage/__init__.py`
- **Collectors**: One class per device in `collectors/`
- **Engine**: Intelligence layer in `engine/` — reminders and supplement recommendations
- **Frontend**: Next.js 14 + TypeScript at `http://localhost:3000` in `dashboard/web/`
- **Config**: `config.yaml` in project root (never committed); user profiles in `users/data/*.yaml`

Data is stored locally by default. There is no cloud sync. Optional API key auth is controlled by the `BIOMONITOR_API_KEY` environment variable.

---

## Architecture Map

```
biomonitor/
├── api_server.py              # ALL FastAPI routes — the single entry point for the API
├── main.py                    # CLI interface
├── config.yaml                # API credentials and settings (not in git)
├── biomonitor.db              # SQLite database (auto-created on first run)
│
├── collectors/
│   ├── __init__.py            # StravaCollector, AppleHealthCollector, CrossFitLogger
│   │                          # + imports OuraCollector, WhoopCollector, XiaomiBandCollector
│   │                          # load_config() and save_config() helpers live here
│   ├── oura.py                # OuraCollector — Personal Access Token auth
│   ├── whoop.py               # WhoopCollector — OAuth 2.0
│   └── xiaomi.py              # XiaomiBandCollector — file export / Gadgetbridge webhook
│
├── engine/
│   ├── __init__.py            # exports RemindersEngine
│   ├── reminders.py           # RemindersEngine: sleep, hydration, standing, fitness, recovery
│   └── supplements.py         # SupplementEngine + Supplement dataclass
│
├── storage/
│   └── __init__.py            # BioDatabase — all SQLite reads and writes
│
├── processors/
│   └── __init__.py            # MetricsCalculator (weekly crossfit/walking aggregations)
│
├── users/
│   ├── __init__.py            # exports load_profile, save_profile, UserProfile
│   ├── profile.py             # UserProfile dataclass + load_profile / save_profile
│   └── data/
│       ├── carl.yaml          # Oura Ring user — endurance focus
│       ├── zelda.yaml         # Xiaomi Mi Band user — general fitness / weight loss
│       ├── zn.yaml            # WHOOP user — muscle gain / recovery
│       └── default.yaml       # Fallback profile
│
├── dashboard/web/
│   ├── app/                   # Next.js App Router pages
│   ├── lib/api.ts             # fetchAPI helper
│   └── package.json
│
└── docs/
    ├── OURA_SETUP.md
    ├── XIAOMI_SETUP.md
    └── WHOOP_SETUP.md
```

---

## Common Tasks

### Add a New Device Collector

1. Create `collectors/{name}.py`. Model the class on `OuraCollector` (in `collectors/oura.py`):
   - `__init__`: read credentials from `load_config()` (and env vars as fallback)
   - `sync_to_database(db: BioDatabase, days: int) -> dict`: fetch data, call `db.save_health_metric()` for every record, return `{metric_type: count}` dict
   - Use `_REQUEST_TIMEOUT = (5, 30)` for every `requests` call
   - Token refresh must call `save_config()` to persist new tokens

2. Add the import at the bottom of `collectors/__init__.py` (before `__all__`) and add the class name to `__all__`.

3. In `api_server.py`:
   - Import and instantiate the collector at the top alongside the others
   - Add routes: `POST /api/{name}/sync`, `GET /api/{name}/stats`, and any OAuth routes if needed
   - Use `Field(ge=1, le=N)` on all numeric query params

4. Create `users/data/{user_id}.yaml` for the primary user of the new device.

5. Create `docs/{NAME}_SETUP.md` with step-by-step auth instructions.

---

### Add a New API Endpoint

Edit `api_server.py` only. Follow these conventions:

- Numeric query params: `param: int = Field(default=X, ge=1, le=N)`
- Time-series reads: `db.get_health_metrics_history(days=days, metric_type="MetricTypeName")`
- Single latest value: `db.get_latest_health_metrics()` (returns dict keyed by friendly name)
- Auth is handled automatically by `auth_middleware` — no per-route auth code needed
- Never expose `client_id` or `client_secret` in any response body (see `GET /api/strava/stats` as the reference pattern)
- Return plain dicts or lists — FastAPI serialises them automatically

---

### Add a New User

1. Create `users/data/{user_id}.yaml` with these fields:

```yaml
user_id: alice
name: Alice
age: 27
weight_kg: 62.0
height_cm: 168.0
sex: female                 # "male" / "female" / "other"
activity_level: active      # "sedentary" / "light" / "moderate" / "active" / "very_active"
device: apple_watch         # "oura" / "whoop" / "xiaomi" / "apple_watch" / "strava_only"
health_goals:
  - sleep
  - general_health
  # Valid values: sleep, recovery, weight_loss, muscle_gain, endurance, general_health
conditions: []
  # e.g.: [hypertension, diabetes, vegetarian]
avg_sleep_hours: null       # filled at runtime from health_metrics DB
avg_hrv: null
avg_resting_hr: null
recovery_score: null
```

2. The profile is immediately accessible via `load_profile("alice")`. No server restart required.

3. To save programmatic changes: `save_profile(profile)` — this is what `PUT /api/users/{user_id}/profile` calls internally.

4. Add the new `user_id` to `_KNOWN_USERS` in `api_server.py` if it should appear in `GET /api/supplements/all-users`.

---

### Modify Supplement Logic

Edit `engine/supplements.py`.

- Each category method (`_sleep_supplements`, `_recovery_supplements`, `_performance_supplements`, `_general_health`, `_female_specific`) receives an enriched `UserProfile` and returns `List[Supplement]`.
- `_deduplicate()` removes duplicate supplement names, keeping the first (highest-priority) occurrence. Order the `supplements.extend(...)` calls in `recommend()` to reflect priority.
- The `Supplement` dataclass fields are: `name`, `dose`, `timing`, `reason`, `evidence_level`, `priority`, `contraindications`.
- Valid `timing` values: `morning`, `pre_workout`, `post_workout`, `evening`, `with_meal`.
- Valid `evidence_level` values: `strong`, `moderate`, `emerging`.
- Valid `priority` values: `essential`, `recommended`, `optional`.
- `as_daily_plan()` groups supplements by timing. Unknown timing strings fall back to `morning`.
- Monthly cost estimates live in `_COST_ESTIMATES` dict at the top of the file.
- Profile enrichment from DB metrics happens in `_enrich_profile()` — it fills `avg_sleep_hours`, `avg_hrv`, `avg_resting_hr`, `recovery_score` from the `health_metrics` table if not already set on the profile YAML.

---

### Modify Reminder Logic

Edit `engine/reminders.py`.

- `RemindersEngine.__init__` takes a `BioDatabase` instance.
- Every method queries the DB via `self.db.get_health_metrics_history(days=N, metric_type="...")`.
- Each public method returns a plain `dict` — these are returned directly by the API routes.
- Standard return shape for a reminder method:
  - Include a human-readable `reason` string
  - Include a `priority` field: `"low"`, `"medium"`, or `"high"`
- `daily_schedule()` merges all other methods into a single `schedule` list sorted by `"HH:MM"` string (24-hour format sorts correctly lexicographically).
- Internal helpers `_parse_hhmm`, `_fmt`, `_add_minutes` are available for time arithmetic.

---

### Add a New Frontend Page

1. Create `dashboard/web/app/{page-name}/page.tsx`:

```tsx
'use client'

import { useEffect, useState } from 'react'
import { fetchAPI } from '@/lib/api'

export default function MyNewPage() {
  const [data, setData] = useState(null)

  useEffect(() => {
    fetchAPI('/api/your-endpoint').then(setData)
  }, [])

  return (
    <main>
      {/* render data */}
    </main>
  )
}
```

2. Add a navigation link in `dashboard/web/app/page.tsx` header.

3. Environment variable for the API base URL: `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). The `fetchAPI` helper in `lib/api.ts` reads it automatically.

---

## API Quick Reference

### Core Activity Endpoints

| Method | Path | Key Params | Description |
|--------|------|-----------|-------------|
| GET | `/api/health` | — | Health check (public, no auth) |
| GET | `/api/activities` | `limit` (1-200), `activity_type` (crossfit\|walking) | List activities |
| GET | `/api/daily` | `days` (1-365) | Daily aggregated chart data |
| GET | `/api/stats/current-week` | — | This week's CrossFit + walking stats |
| GET | `/api/stats/weekly` | `weeks` (1-52) | Last N weeks aggregated stats |
| GET | `/api/crossfit/workouts` | `limit` (1-100) | Recent CrossFit workouts |
| POST | `/api/crossfit/log` | JSON body (CrossFitWorkout) | Log a workout manually |
| POST | `/api/activities/sync` | JSON body (Activity) | Sync a single activity |

### Strava

| Method | Path | Key Params | Description |
|--------|------|-----------|-------------|
| POST | `/api/strava/sync` | `days` (1-365) | Sync Strava activities |
| GET | `/api/strava/stats` | — | Connection status (no credentials exposed) |

### Apple Health

| Method | Path | Key Params | Description |
|--------|------|-----------|-------------|
| POST | `/api/apple-health/webhook` | JSON body | Receive Health Auto Export push |
| GET | `/api/health-metrics/latest` | — | Latest HR, HRV, sleep, steps |
| GET | `/api/health-metrics/history` | `days` (1-365), `metric_type` | Time-series metric history |
| GET | `/api/apple-health/formats` | — | Supported HealthKit metric format docs |

### Oura Ring (Carl)

| Method | Path | Key Params | Description |
|--------|------|-----------|-------------|
| POST | `/api/oura/sync` | `days` (1-90) | Sync Oura data |
| GET | `/api/oura/readiness` | `days` (1-90) | Readiness score history |
| GET | `/api/oura/sleep` | `days` (1-90) | Sleep score + duration history |

### WHOOP (ZN)

| Method | Path | Key Params | Description |
|--------|------|-----------|-------------|
| GET | `/api/whoop/auth-url` | — | Get OAuth authorization URL |
| POST | `/api/whoop/callback` | `{"code": "..."}` | Exchange OAuth code for tokens |
| POST | `/api/whoop/sync` | `days` (1-90) | Sync WHOOP data |
| GET | `/api/whoop/recovery` | `days` (1-90) | Recovery score history |
| GET | `/api/whoop/strain` | `days` (1-90) | Strain score history |

### Xiaomi Mi Band (Zelda)

| Method | Path | Key Params | Description |
|--------|------|-----------|-------------|
| POST | `/api/xiaomi/upload` | JSON body (`format`, `data`) | Upload Mi Fitness or Gadgetbridge export |
| POST | `/api/xiaomi/webhook` | JSON body (XiaomiWebhookData) | Real-time Gadgetbridge HTTP server data |
| GET | `/api/xiaomi/stats` | `days` (1-90) | Xiaomi metrics from DB |

### Smart Reminders

| Method | Path | Key Params | Description |
|--------|------|-----------|-------------|
| GET | `/api/reminders/sleep` | — | Bedtime / wake time recommendation |
| GET | `/api/reminders/hydration` | `wake_time`, `sleep_time` | Hourly hydration schedule |
| GET | `/api/reminders/standing` | `work_start`, `work_end` | Stand-up reminders during work hours |
| GET | `/api/reminders/fitness` | `weekly_target` (1-7) | Workout or rest recommendation |
| GET | `/api/reminders/recovery` | — | Recovery score (0-100) from WHOOP/Oura/HRV |
| GET | `/api/reminders/daily` | `wake_time`, `sleep_time`, `work_start`, `work_end` | Full merged daily schedule |

### User Profiles and Supplements

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/users/{user_id}/profile` | Get user profile |
| PUT | `/api/users/{user_id}/profile` | Partial-update user profile |
| GET | `/api/users/{user_id}/supplements` | Flat supplement list for user |
| GET | `/api/users/{user_id}/supplements/daily-plan` | Supplements grouped by timing |
| GET | `/api/supplements/all-users` | All users' supplement plans side by side |
| GET | `/api/share/card` | Share card data (current week stats + latest health) |

---

## Data Model

### SQLite Tables

**`health_metrics`** — the single write target for all wearable data:

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | auto |
| `date` | TIMESTAMP | ISO-8601 string |
| `metric_type` | TEXT | see strings below |
| `value` | REAL | numeric value |
| `unit` | TEXT | e.g. `"count/min"`, `"ms"`, `"kcal"` |
| `source` | TEXT | `"apple_health"`, `"oura"`, `"whoop"`, `"xiaomi_band"` |
| `created_at` | TIMESTAMP | auto |

**`activities`** — Strava and manually synced workouts. Key columns: `strava_id` (UNIQUE), `is_crossfit` (BOOLEAN), `is_walking` (BOOLEAN), `start_date`, `distance` (meters), `moving_time` (seconds).

**`crossfit_workouts`** — manually logged WODs via `POST /api/crossfit/log`.

**`daily_summaries`** — pre-aggregated daily cache (updated by the processors).

### Metric Type Strings

All `metric_type` values used across the codebase:

| Source | metric_type |
|--------|-------------|
| Apple Health / Apple Watch | `HeartRate` |
| Apple Health / Apple Watch | `HeartRateVariability` (legacy key in `get_latest_health_metrics`) |
| Apple Health / Apple Watch | `HeartRateVariabilitySDNN` (used for history queries, HRV trending, and supplement engine) |
| Apple Health / Apple Watch | `SleepAnalysis` |
| Apple Health / Apple Watch | `StepCount` |
| Apple Health / Apple Watch | `ActiveEnergyBurned` |
| Apple Health / Apple Watch | `OxygenSaturation` |
| Apple Health / Apple Watch | `AppleSleepingWristTemperature` |
| Oura Ring | `OuraReadiness` |
| Oura Ring | `OuraSleepScore` |
| Oura Ring | `OuraSleepDuration` (stored in **seconds**; divide by 3600 for hours) |
| WHOOP | `WhoopRecovery` (0-100 scale) |
| WHOOP | `WhoopSleepScore` |
| WHOOP | `WhoopStrain` |
| Xiaomi Mi Band | `StepCount` (source field = `"xiaomi_band"`) |
| Xiaomi Mi Band | `HeartRate` (source field = `"xiaomi_band"`) |
| Xiaomi Mi Band | `SleepAnalysis` (source field = `"xiaomi_band"`) |
| Xiaomi Mi Band | `ActiveEnergyBurned` (source field = `"xiaomi_band"`) |

---

## Config Reference

`config.yaml` structure covering all five integrations:

```yaml
strava:
  client_id: "your_strava_client_id"
  client_secret: "your_strava_client_secret"
  access_token: "your_strava_access_token"
  refresh_token: "your_strava_refresh_token"

apple_health:
  export_path: "/tmp/apple_health_exports"  # where webhook JSON files are saved
  webhook_enabled: true

oura:
  access_token: "your_oura_personal_access_token"  # no OAuth — Personal Access Token only

whoop:
  client_id: "your_whoop_client_id"
  client_secret: "your_whoop_client_secret"
  access_token: "your_whoop_access_token"      # written automatically after OAuth
  refresh_token: "your_whoop_refresh_token"    # written automatically after OAuth
  redirect_uri: "http://localhost:8000/api/whoop/callback"

xiaomi:
  account_email: "your_xiaomi_account_email"
  password: "your_xiaomi_password"             # or use file export via Gadgetbridge
```

All sections are optional. A missing section disables the corresponding integration gracefully — the collector returns a `"skipped"` key in its result dict rather than raising.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BIOMONITOR_API_KEY` | (unset) | If set, all requests except `/api/health` require `X-API-Key` header |
| `BIOMONITOR_HOST` | `127.0.0.1` | Server bind address |
| `BIOMONITOR_PORT` | `8000` | Server port |
| `FRONTEND_URL` | (unset) | Additional CORS origin added to the allowed list |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend API base URL |
| `NEXT_PUBLIC_API_KEY` | (unset) | Frontend API key |

---

## User Profiles

Profiles are stored as YAML in `users/data/{user_id}.yaml` and loaded with `load_profile(user_id)` from `users/__init__.py`.

| user_id | Name | Device | Activity Level | Health Goals |
|---------|------|--------|---------------|-------------|
| `carl` | Carl | oura | active | sleep, recovery, endurance |
| `zelda` | Zelda | xiaomi | moderate | sleep, weight_loss, general_health |
| `zn` | ZN | whoop | very_active | muscle_gain, recovery, endurance |
| `default` | Default | — | — | fallback profile |

The `UserProfile` dataclass (in `users/profile.py`) has these fields:

- Required: `user_id`, `name`, `age`, `weight_kg`, `height_cm`, `sex`, `activity_level`, `device`, `health_goals`, `conditions`
- Computed at runtime (null in YAML, filled from DB): `avg_sleep_hours`, `avg_hrv`, `avg_resting_hr`, `recovery_score`

Valid `health_goals` values: `sleep`, `recovery`, `weight_loss`, `muscle_gain`, `endurance`, `general_health`

Valid `activity_level` values: `sedentary`, `light`, `moderate`, `active`, `very_active`

Valid `device` values: `oura`, `whoop`, `xiaomi`, `apple_watch`, `strava_only`

---

## Key Patterns to Follow

**HTTP requests** — always use the module-level timeout constant:
```python
_REQUEST_TIMEOUT = (5, 30)  # connect_timeout, read_timeout
requests.get(url, timeout=_REQUEST_TIMEOUT)
```

**Token refresh** — always persist updated tokens back to disk immediately:
```python
config = load_config()
config['whoop']['access_token'] = new_token
save_config(config)
```

**Numeric query params** — always bound with `Field`:
```python
days: int = Field(default=30, ge=1, le=365)
limit: int = Field(default=10, ge=1, le=100)
```

**Writing health data** — `db.save_health_metric()` is the single write path for all wearable data regardless of source. Always pass a dict with at minimum `date`, `metric_type`, `value`, `unit`, `source`.

**New collectors** — always go in `collectors/` and must be exported via `__all__` in `collectors/__init__.py`.

**Strava date handling** — Strava timestamps are UTC-aware. Convert timezone with `tz_convert(None)`, not `tz_localize(None)`. Using `tz_localize(None)` on an already-tz-aware Series raises a TypeError.

**Immutability** — `_enrich_profile()` in `engine/supplements.py` is the canonical example: use `dataclasses.replace(profile, **updates)` to return a new object rather than mutating the existing one.

**Webhook payload size** — the Apple Health webhook is limited to 5 MB (`_WEBHOOK_MAX_BYTES`). This is enforced in `auth_middleware` before the route handler runs.

---

## Do Not

- **Hardcode health metric values** — all metric values must come from the database or live API responses. This was the original bug that motivated the project's DB-first design.
- **Expose `client_id` or `client_secret` in any API response** — follow the `GET /api/strava/stats` pattern which returns only `{"connected": bool}`.
- **Use `tz_localize(None)` on Strava dates** — use `tz_convert(None)` instead (see `get_weekly_stats` in `api_server.py`).
- **Bind the server to `0.0.0.0` without setting `BIOMONITOR_API_KEY`** — the default bind address is `127.0.0.1` for this reason. Warn the user if they try to expose the server publicly without auth.
- **Add new tables or columns without updating `BioDatabase.init_database()`** — schema migrations happen there via `CREATE TABLE IF NOT EXISTS`.
- **Skip `__all__` when adding to `collectors/__init__.py`** — downstream imports in `api_server.py` rely on the explicit export list.
