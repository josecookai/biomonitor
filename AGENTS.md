# BioMonitor — Codex Agent Guide

> This file teaches Codex how to work with the BioMonitor codebase.
> Read this entire file before making any changes.

---

## Project Overview

BioMonitor is an open-source personal health dashboard that aggregates fitness and wellness data from five wearable devices and services into a single unified interface. It syncs data from **Strava**, **Oura Ring**, **WHOOP**, **Apple Health** (via webhook), and **Xiaomi Mi Band**, then surfaces the data through a REST API and a Next.js dashboard.

**Tech stack:**
- Backend: Python 3.10+, FastAPI, SQLite (via `BioDatabase`)
- Frontend: Next.js 14, TypeScript
- Device integrations: five collector classes, each in `collectors/`
- Intelligence layer: `RemindersEngine` (sleep, hydration, standing, fitness, recovery) and `SupplementEngine` (profile-driven supplement recommendations)

**Three named users ship with the project:**
- **Carl** — Oura Ring, endurance focus
- **Zelda** — Xiaomi Mi Band, general fitness
- **ZN** — WHOOP, recovery and performance

All API credentials live in `config.yaml` (never committed). The server starts unauthenticated by default; set `BIOMONITOR_API_KEY` to lock every endpoint behind an `X-API-Key` header.

---

## Repository Layout

```
biomonitor/
├── api_server.py          # FastAPI app — ALL routes defined here; entry point
├── main.py                # CLI interface
├── config.yaml            # Secrets — never commit (in .gitignore)
├── config.example.yaml    # Safe template — the only config file to commit
├── requirements.txt       # Python deps
├── setup_demo.py          # Loads demo data into the DB
├── biomonitor.db          # SQLite database (auto-created on first run)
│
├── collectors/
│   ├── __init__.py        # StravaCollector, AppleHealthCollector, CrossFitLogger
│   │                      #   + load_config(), save_config(), _REQUEST_TIMEOUT
│   ├── oura.py            # OuraCollector — Oura v2 REST API (Carl's device)
│   ├── whoop.py           # WhoopCollector — WHOOP OAuth2 API (ZN's device)
│   └── xiaomi.py          # XiaomiBandCollector — Gadgetbridge/Mi Fitness (Zelda's device)
│
├── engine/
│   ├── __init__.py        # Exports RemindersEngine, Supplement, SupplementEngine
│   ├── reminders.py       # RemindersEngine — sleep/hydration/standing/fitness/recovery logic
│   └── supplements.py     # SupplementEngine + Supplement dataclass; _enrich_profile() helper
│
├── storage/
│   └── __init__.py        # BioDatabase — all SQLite CRUD; exports BioDatabase
│
├── processors/
│   └── __init__.py        # MetricsCalculator, TrendAnalyzer
│
├── users/
│   ├── __init__.py        # Re-exports UserProfile, load_profile, save_profile
│   ├── profile.py         # UserProfile dataclass + load_profile() / save_profile()
│   └── data/
│       ├── carl.yaml      # Carl's profile — Oura Ring, endurance
│       ├── zelda.yaml     # Zelda's profile — Xiaomi Mi Band, general fitness
│       ├── zn.yaml        # ZN's profile — WHOOP, recovery/performance
│       └── default.yaml   # Fallback profile for unknown user_id lookups
│
├── dashboard/web/
│   ├── app/
│   │   ├── page.tsx           # Main dashboard (activity heatmap, weekly stats)
│   │   ├── activity/page.tsx  # Activity analysis
│   │   ├── recovery/page.tsx  # Recovery metrics (WHOOP + Oura)
│   │   ├── reminders/page.tsx # Smart reminders timeline
│   │   └── supplements/page.tsx # Supplement recommendations
│   ├── lib/
│   │   └── api.ts             # fetchAPI() helper + all TypeScript interfaces
│   └── package.json
│
└── docs/
    ├── OURA_SETUP.md      # Carl's Oura Personal Access Token setup guide
    ├── WHOOP_SETUP.md     # ZN's WHOOP OAuth2 developer app setup guide
    └── XIAOMI_SETUP.md    # Zelda's Gadgetbridge / Mi Fitness export guide
```

---

## Database Schema

The database is auto-created at startup via `BioDatabase.init_database()`. There are five tables:

### `health_metrics` — central metrics store (most important)

```sql
CREATE TABLE IF NOT EXISTS health_metrics (
    id          INTEGER PRIMARY KEY,
    date        TIMESTAMP,
    metric_type TEXT,   -- see Metric Types section below
    value       REAL,
    unit        TEXT,
    source      TEXT,   -- 'oura', 'whoop', 'apple_health', 'xiaomi_band', 'strava'
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `activities` — Strava + manually synced workouts

```sql
CREATE TABLE IF NOT EXISTS activities (
    id                   INTEGER PRIMARY KEY,
    strava_id            BIGINT UNIQUE,
    name                 TEXT,
    type                 TEXT,
    sport_type           TEXT,
    start_date           TIMESTAMP,
    distance             REAL,
    moving_time          INTEGER,
    elapsed_time         INTEGER,
    average_speed        REAL,
    max_speed            REAL,
    average_heartrate    REAL,
    max_heartrate        REAL,
    total_elevation_gain REAL,
    is_crossfit          BOOLEAN,
    is_walking           BOOLEAN,
    raw_data             TEXT,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `crossfit_workouts` — manually logged WODs

```sql
CREATE TABLE IF NOT EXISTS crossfit_workouts (
    id         INTEGER PRIMARY KEY,
    date       TIMESTAMP,
    wod_name   TEXT,
    time       TEXT,    -- finish time string e.g. "4:52"
    rounds     INTEGER,
    reps       INTEGER,
    weight     REAL,
    rpe        INTEGER, -- rate of perceived exertion 1-10
    notes      TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `daily_summaries` and `settings` — auxiliary tables (rarely queried directly)

---

## Metric Type Strings

Use **exactly** these strings for `metric_type` when calling `db.save_health_metric()` or `db.get_health_metrics_history()`:

| metric_type string | Description | Unit | Primary source |
|--------------------|-------------|------|----------------|
| `HeartRate` | Resting or active heart rate | bpm | oura, whoop, apple_health, xiaomi_band |
| `HeartRateVariability` | HRV RMSSD | ms | oura, whoop |
| `HeartRateVariabilitySDNN` | HRV SDNN (Apple Watch variant) | ms | apple_health |
| `SleepAnalysis` | Sleep duration | hours | whoop, apple_health, xiaomi_band |
| `StepCount` | Daily steps | steps | apple_health, xiaomi_band |
| `ActiveEnergyBurned` | Active calories burned | kcal | apple_health, xiaomi_band |
| `OuraReadiness` | Oura daily readiness score | score (0-100) | oura |
| `OuraSleepScore` | Oura sleep score | score (0-100) | oura |
| `OuraSleepDuration` | Oura total sleep duration | seconds | oura |
| `OuraActivityScore` | Oura daily activity score | score (0-100) | oura |
| `WhoopRecovery` | WHOOP recovery score | score (0-100) | whoop |
| `WhoopStrain` | WHOOP strain score | strain (0-21) | whoop |
| `WhoopSleepScore` | WHOOP sleep performance | % | whoop |

> The `RemindersEngine` queries `HeartRateVariabilitySDNN` (Apple Watch) not `HeartRateVariability`. Keep this distinction when adding new collectors.

---

## Key API Routes

All routes are defined in `api_server.py`. There are no route files elsewhere.

### Activities & Stats
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/activities` | List activities; params: `limit` (1-200), `activity_type` (crossfit\|walking) |
| GET | `/api/daily` | Daily aggregated data for charts; param: `days` (1-365) |
| GET | `/api/stats/current-week` | Current week CrossFit + walking stats |
| GET | `/api/stats/weekly` | Last N weeks of stats; param: `weeks` (1-52) |

### CrossFit
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/crossfit/workouts` | Recent WODs; param: `limit` (1-100) |
| POST | `/api/crossfit/log` | Log a WOD; body: `CrossFitWorkout` model |

### Device Sync
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/strava/sync` | Sync Strava; param: `days` (1-365) |
| POST | `/api/oura/sync` | Sync Oura; param: `days` (1-90) |
| POST | `/api/whoop/sync` | Sync WHOOP; param: `days` (1-90) |
| POST | `/api/xiaomi/upload` | Upload Gadgetbridge/Mi Fitness export JSON |
| POST | `/api/xiaomi/webhook` | Real-time Gadgetbridge HTTP server push |
| POST | `/api/apple-health/webhook` | Health Auto Export webhook |

### Health Metrics
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health-metrics/latest` | Most recent HR, HRV, sleep, steps |
| GET | `/api/health-metrics/history` | Metric history; params: `days`, `metric_type` |
| GET | `/api/oura/readiness` | OuraReadiness records; param: `days` |
| GET | `/api/oura/sleep` | OuraSleepScore + OuraSleepDuration; param: `days` |
| GET | `/api/whoop/recovery` | WhoopRecovery records; param: `days` |
| GET | `/api/whoop/strain` | WhoopStrain records; param: `days` |
| GET | `/api/xiaomi/stats` | Xiaomi steps, HR, sleep, calories; param: `days` |

### WHOOP OAuth
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/whoop/auth-url` | Returns the OAuth2 authorization URL |
| POST | `/api/whoop/callback` | Exchanges authorization code for tokens; body: `{"code": "..."}` |

### Reminders
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/reminders/sleep` | Bedtime / wake recommendation |
| GET | `/api/reminders/hydration` | Hourly hydration schedule; params: `wake_time`, `sleep_time` |
| GET | `/api/reminders/standing` | Standing reminders; params: `work_start`, `work_end` |
| GET | `/api/reminders/fitness` | Workout scheduling; param: `weekly_target` (1-7) |
| GET | `/api/reminders/recovery` | Recovery score 0-100 from WHOOP/Oura/HRV |
| GET | `/api/reminders/daily` | Full merged daily timeline |

### User Profiles & Supplements
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/users/{user_id}/profile` | Load a user's YAML profile |
| PUT | `/api/users/{user_id}/profile` | Merge partial updates into profile |
| GET | `/api/users/{user_id}/supplements` | Flat list of personalised recommendations |
| GET | `/api/users/{user_id}/supplements/daily-plan` | Supplements grouped by timing |
| GET | `/api/supplements/all-users` | Recommendations for all known users side-by-side |

### Infrastructure
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check — always public, no auth |
| GET | `/api/share/card` | Generate share card data |

---

## Writing a New Collector

1. Create `collectors/{name}.py`.
2. Follow this structure exactly:

```python
# collectors/newdevice.py
import requests
from typing import List, Dict
from . import load_config, save_config, _REQUEST_TIMEOUT


class NewDeviceCollector:
    def __init__(self, access_token: str = None):
        config = load_config()
        cfg = config.get('newdevice', {})
        self.access_token = access_token or cfg.get('access_token')
        self.base_url = "https://api.newdevice.com/v1"

    def get_data(self, start_date: str, end_date: str) -> List[Dict]:
        resp = requests.get(
            f"{self.base_url}/endpoint",
            headers={"Authorization": f"Bearer {self.access_token}"},
            params={"start": start_date, "end": end_date},
            timeout=_REQUEST_TIMEOUT,  # always use the shared constant
        )
        resp.raise_for_status()
        return resp.json()

    def sync_to_database(self, db, days: int = 7) -> Dict[str, int]:
        if not self.access_token:
            return {"skipped": "no access token configured"}
        # ... compute date range, iterate records ...
        db.save_health_metric({
            "date": record["date"],
            "metric_type": "HeartRate",  # must match Metric Type Strings table
            "value": float(record["value"]),
            "unit": "bpm",
            "source": "newdevice",
        })
        return {"HeartRate": saved_count}
```

3. Register in `collectors/__init__.py`:

```python
from .newdevice import NewDeviceCollector

__all__ = [..., 'NewDeviceCollector']
```

4. Instantiate in `api_server.py` at module level (alongside the other collectors):

```python
from collectors import ..., NewDeviceCollector
newdevice_collector = NewDeviceCollector()
```

5. Add sync and query routes following the patterns in the `# ========== OURA RING ==========` block.

---

## Writing a New API Route

```python
from pydantic import Field

# Bounded numeric query params — always use Field with ge/le
@app.get("/api/newdevice/data")
def get_newdevice_data(days: int = Field(default=7, ge=1, le=90)):
    return db.get_health_metrics_history(days=days, metric_type="HeartRate")

# Standard error handling pattern
@app.post("/api/newdevice/sync")
def sync_newdevice(days: int = Field(default=7, ge=1, le=90)):
    try:
        counts = newdevice_collector.sync_to_database(db, days)
        if "skipped" in counts:
            raise HTTPException(status_code=503, detail=counts["skipped"])
        return {"success": True, "days": days, "synced": counts}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(exc)}")
```

---

## Adding a New User Profile

1. Create `users/data/{user_id}.yaml` following this schema:

```yaml
user_id: newuser
name: "Display Name"
age: 30
weight_kg: 70.0
height_cm: 175.0
sex: "male"          # "male" / "female" / "other"
activity_level: "active"  # sedentary / light / moderate / active / very_active
device: "oura"       # oura / whoop / xiaomi / apple_watch / strava_only
health_goals:
  - "recovery"       # sleep / recovery / weight_loss / muscle_gain / endurance / general_health
conditions: []       # hypertension / diabetes / vegetarian / ...
# Leave computed fields absent — they are filled from the DB at runtime:
# avg_sleep_hours, avg_hrv, avg_resting_hr, recovery_score
```

2. Add the `user_id` string to `_KNOWN_USERS` in `api_server.py`:

```python
_KNOWN_USERS = ["carl", "zelda", "zn", "default", "newuser"]
```

---

## Frontend Conventions

All API calls go through `fetchAPI` from `dashboard/web/lib/api.ts`. Never call `fetch` directly in page components.

```typescript
import { fetchAPI } from '@/lib/api'

// Always define interfaces — never use `any`
interface MyData {
  id: number
  value: number
  date: string
}

// Standard page pattern
const [data, setData] = useState<MyData | null>(null)
const [loading, setLoading] = useState(true)
const [error, setError] = useState<string | null>(null)

useEffect(() => {
  fetchAPI<MyData>('/api/endpoint')
    .then(setData)
    .catch(e => setError(e.message))
    .finally(() => setLoading(false))
}, [])

if (loading) return <div>Loading...</div>
if (error) return <div>Error: {error}</div>
```

---

## `UserProfile` Dataclass Fields

Defined in `users/profile.py`. All fields are available on every profile object:

| Field | Type | Notes |
|-------|------|-------|
| `user_id` | str | Matches the YAML filename stem |
| `name` | str | Display name |
| `age` | int | |
| `weight_kg` | float | Used by SupplementEngine for protein target |
| `height_cm` | float | |
| `sex` | str | `"male"` / `"female"` / `"other"` — controls female-specific supplements |
| `activity_level` | str | `sedentary` / `light` / `moderate` / `active` / `very_active` |
| `device` | str | Primary wearable |
| `health_goals` | List[str] | Drives supplement and reminder categories |
| `conditions` | List[str] | Medical/dietary conditions |
| `avg_sleep_hours` | Optional[float] | Computed from DB at request time |
| `avg_hrv` | Optional[float] | Computed from DB at request time |
| `avg_resting_hr` | Optional[float] | Computed from DB at request time |
| `recovery_score` | Optional[float] | Computed from DB at request time |

The `_enrich_profile()` helper in `engine/supplements.py` fills the four computed fields from live DB data via `dataclasses.replace()` (immutable update — never mutate the profile in-place).

---

## `SupplementEngine` Category Triggers

Understanding when each supplement category fires helps when adding new categories:

| Category method | Fires when |
|-----------------|-----------|
| `_sleep_supplements` | `avg_sleep_hours < 7` OR `"sleep" in health_goals` |
| `_recovery_supplements` | `recovery_score < 60` OR `avg_hrv < 40` OR `"recovery" in health_goals` |
| `_performance_supplements` | `health_goals` intersects `{muscle_gain, endurance}` AND `activity_level` in `{active, very_active}` |
| `_general_health` | Always |
| `_female_specific` | `profile.sex == "female"` |

Supplements with duplicate names are deduplicated; the first occurrence (highest priority) wins.

---

## `RemindersEngine` Methods

All methods are on `RemindersEngine(db)` in `engine/reminders.py`:

| Method | Route | Returns |
|--------|-------|---------|
| `sleep_recommendation()` | `/api/reminders/sleep` | `recommended_bedtime`, `recommended_wake`, `current_avg_hours`, `priority` |
| `hydration_schedule(wake_time, sleep_time)` | `/api/reminders/hydration` | Daily glass schedule with times and notes |
| `standing_reminders(work_start, work_end)` | `/api/reminders/standing` | Stand-up prompts every 50 min; flags low step count |
| `fitness_reminders(weekly_target)` | `/api/reminders/fitness` | `today_recommendation` in `workout/rest/active_recovery` |
| `rest_recommendation()` | `/api/reminders/recovery` | Composite score 0-100 from WHOOP + Oura + HRV |
| `daily_schedule(...)` | `/api/reminders/daily` | All reminders merged and sorted by HH:MM |

---

## Common Tasks Reference

| Task | Files to edit | Key function / class |
|------|--------------|----------------------|
| Add a new device integration | `collectors/{name}.py`, `collectors/__init__.py`, `api_server.py` | `sync_to_database()` |
| Add a new user | `users/data/{id}.yaml`, `api_server.py` (`_KNOWN_USERS`) | `load_profile()` / `save_profile()` |
| Add a new reminder type | `engine/reminders.py` | New method on `RemindersEngine` + route in `api_server.py` |
| Add a supplement category | `engine/supplements.py` | New `_category_supplements()` method; call from `recommend()` |
| Add a new API route | `api_server.py` | `@app.get` / `@app.post` with `Field` bounds |
| Add a new frontend page | `dashboard/web/app/{name}/page.tsx` | `fetchAPI<T>()` from `lib/api.ts` |
| Save a health metric | `storage/__init__.py` (read-only) | `db.save_health_metric({...})` |
| Query health metrics | `storage/__init__.py` (read-only) | `db.get_health_metrics_history(days, metric_type)` |
| Persist refreshed OAuth tokens | Already handled by `_persist_tokens()` in each collector | Call `save_config(config)` |

---

## Critical Rules — Never Violate

1. **Never return `client_secret` or `client_id` in API responses.** Credentials stay server-side only.
2. **Never use `dt.tz_localize(None)` on Strava timestamps** — Strava timestamps are UTC-aware; use `dt.tz_convert(None)` to strip timezone.
3. **Never hardcode health metric values** — always query from the DB via `db.get_health_metrics_history()`.
4. **Never bind the server to `0.0.0.0` without `BIOMONITOR_API_KEY` set.** The default bind is `127.0.0.1`.
5. **Always use `timeout=_REQUEST_TIMEOUT`** (i.e., `(5, 30)`) on every outbound `requests.get/post` call.
6. **Always persist refreshed tokens** via `save_config(config)` after any successful token refresh.
7. **Always use `Field(ge=1, le=N)` for bounded query parameters** — never accept unbounded integers from the client.
8. **Never commit `config.yaml`** — only `config.example.yaml` is safe to commit.
9. **Never mutate a `UserProfile` in-place** — use `dataclasses.replace(profile, **updates)` for all profile updates.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BIOMONITOR_API_KEY` | (unset) | When set, all requests except `/api/health` require `X-API-Key` header |
| `BIOMONITOR_HOST` | `127.0.0.1` | Server bind address |
| `BIOMONITOR_PORT` | `8000` | Server port |
| `FRONTEND_URL` | (unset) | Extra CORS origin added at startup |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend API base URL |
| `NEXT_PUBLIC_API_KEY` | (unset) | Frontend API key |

---

## Running the Project

```bash
# Backend (from project root)
cp config.example.yaml config.yaml   # first time only
pip install -r requirements.txt
python api_server.py
# API: http://localhost:8000
# Docs: http://localhost:8000/docs

# Frontend (separate terminal)
cd dashboard/web
npm install
npm run dev
# UI: http://localhost:3000

# Demo data
python setup_demo.py
```

---

## Config File Structure (`config.yaml`)

```yaml
strava:
  client_id: ""
  client_secret: ""
  access_token: ""
  refresh_token: ""

apple_health:
  export_path: "/tmp/apple_health_exports"
  webhook_enabled: true

oura:
  access_token: ""        # Personal Access Token from cloud.ouraring.com

whoop:
  client_id: ""
  client_secret: ""
  redirect_uri: "http://localhost:8000/api/whoop/callback"
  access_token: ""        # Written automatically by OAuth flow
  refresh_token: ""       # Written automatically by OAuth flow

xiaomi:
  account_email: ""
  password: ""            # Or use Gadgetbridge JSON export instead
```

All keys are optional. A missing section disables that integration gracefully — collectors return `{"skipped": "..."}` rather than raising.
