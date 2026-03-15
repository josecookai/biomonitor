import pandas as pd
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import BioDatabase
from processors import MetricsCalculator
from collectors import StravaCollector, AppleHealthCollector, OuraCollector, WhoopCollector, XiaomiBandCollector
from users import load_profile, save_profile, UserProfile
from engine.supplements import SupplementEngine

app = FastAPI(
    title="BioMonitor API",
    description="Health metrics tracking API",
    version="0.1.0"
)

# CORS for frontend - Support both local and Railway
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://biomonitor-web-production.up.railway.app",
    "https://*.railway.app"  # Allow all Railway subdomains
]

# Add custom origin from env var if set
if os.getenv("FRONTEND_URL"):
    ALLOWED_ORIGINS.append(os.getenv("FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Optional API key authentication
# Set BIOMONITOR_API_KEY env var to enable. If unset, auth is disabled
# (suitable for local-only dev). Never expose the server on 0.0.0.0 without
# setting this variable.
# ---------------------------------------------------------------------------
_API_KEY = os.environ.get("BIOMONITOR_API_KEY", "").strip()
_PUBLIC_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc"}

_WEBHOOK_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Skip auth for public paths
    if request.url.path in _PUBLIC_PATHS:
        return await call_next(request)

    # If API key is configured, enforce it on every request
    if _API_KEY:
        client_key = request.headers.get("X-API-Key", "")
        if client_key != _API_KEY:
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})

    # Enforce payload size limit on webhook
    if request.url.path == "/api/apple-health/webhook":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > _WEBHOOK_MAX_BYTES:
            return JSONResponse(status_code=413, content={"detail": "Payload too large"})

    return await call_next(request)


# Initialize database and collectors
db = BioDatabase()
strava_collector = StravaCollector()
apple_collector = AppleHealthCollector()
oura_collector = OuraCollector()
whoop_collector = WhoopCollector()
xiaomi_collector = XiaomiBandCollector()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class CrossFitWorkout(BaseModel):
    wod_name: str
    date: str
    time: Optional[str] = None
    rounds: Optional[int] = None
    reps: Optional[int] = None
    weight: Optional[float] = None
    rpe: Optional[int] = None
    notes: Optional[str] = None


class HealthAutoExportData(BaseModel):
    """Health Auto Export webhook data"""
    data: List[Dict[str, Any]]
    metadata: Optional[Dict] = None


class XiaomiExportData(BaseModel):
    """Mi Fitness or Gadgetbridge export data (JSON array)"""
    format: str  # "gadgetbridge" or "mi_fitness"
    data: List[Dict[str, Any]]


class XiaomiWebhookData(BaseModel):
    """Real-time payload from Gadgetbridge HTTP server plugin"""
    timestamp: Optional[int] = None
    heart_rate: Optional[int] = None
    steps: Optional[int] = None
    battery: Optional[int] = None
    activity: Optional[str] = None


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/activities")
def get_activities(
    limit: int = Field(default=30, ge=1, le=200),
    activity_type: Optional[str] = None
):
    """Get recent activities"""
    df = db.get_activities(limit=limit)

    if df.empty:
        return []

    if activity_type:
        if activity_type == "crossfit":
            df = df[df['is_crossfit'] == True]
        elif activity_type == "walking":
            df = df[df['is_walking'] == True]

    activities = []
    for _, row in df.iterrows():
        activities.append({
            "id": int(row['id']),
            "name": row['name'],
            "type": row['type'],
            "start_date": row['start_date'],
            "distance": float(row['distance']) if pd.notna(row['distance']) else None,
            "moving_time": int(row['moving_time']),
            "average_heartrate": float(row['average_heartrate']) if pd.notna(row['average_heartrate']) else None,
            "max_heartrate": float(row['max_heartrate']) if pd.notna(row['max_heartrate']) else None,
            "is_crossfit": bool(row['is_crossfit']),
            "is_walking": bool(row['is_walking'])
        })

    return activities


@app.get("/api/stats/weekly")
def get_weekly_stats(weeks: int = Field(default=4, ge=1, le=52)):
    """Get weekly aggregated stats"""
    df = db.get_activities()

    if df.empty:
        return []

    df['start_date'] = pd.to_datetime(df['start_date'], utc=True).dt.tz_convert(None)
    df['week'] = df['start_date'].dt.isocalendar().week
    df['year'] = df['start_date'].dt.isocalendar().year

    weekly_stats = []

    for (year, week), group in df.groupby(['year', 'week']):
        crossfit_count = group[group['is_crossfit'] == True].shape[0]
        walking_df = group[group['is_walking'] == True]
        walking_distance = walking_df['distance'].sum() / 1000  # km
        walking_time = walking_df['moving_time'].sum() / 60  # min

        weekly_stats.append({
            "week": f"{year}-W{week:02d}",
            "crossfit_sessions": int(crossfit_count),
            "walking_distance_km": round(walking_distance, 2),
            "walking_time_min": round(walking_time, 0),
            "total_activities": len(group)
        })

    return weekly_stats[-weeks:]


@app.get("/api/stats/current-week")
def get_current_week_stats():
    """Get current week statistics"""
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)

    df = db.get_activities(week_start, week_end)

    if df.empty:
        return {
            "week_start": week_start.strftime("%Y-%m-%d"),
            "crossfit_sessions": 0,
            "walking_distance_km": 0,
            "walking_time_min": 0,
            "total_activities": 0
        }

    calculator = MetricsCalculator(df)
    crossfit_count = calculator.weekly_crossfit_count(week_start)
    walking_stats = calculator.weekly_walking_stats(week_start)

    return {
        "week_start": week_start.strftime("%Y-%m-%d"),
        "crossfit_sessions": crossfit_count,
        "walking_distance_km": walking_stats['total_distance_km'],
        "walking_time_min": walking_stats['total_time_min'],
        "total_activities": len(df)
    }


@app.get("/api/daily")
def get_daily_data(days: int = Field(default=30, ge=1, le=365)):
    """Get daily aggregated data for charts"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    df = db.get_activities(start_date, end_date)

    if df.empty:
        return []

    df['start_date'] = pd.to_datetime(df['start_date'], utc=True).dt.tz_convert(None)
    df['date'] = df['start_date'].dt.date

    daily_data = []

    for date, group in df.groupby('date'):
        crossfit_count = group[group['is_crossfit'] == True].shape[0]
        walking_df = group[group['is_walking'] == True]
        walking_distance = walking_df['distance'].sum() / 1000

        daily_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "crossfit": int(crossfit_count),
            "walking": round(walking_distance, 2)
        })

    return daily_data


@app.post("/api/crossfit/log")
def log_crossfit_workout(workout: CrossFitWorkout):
    """Log a CrossFit workout"""
    try:
        workout_id = db.save_crossfit_workout(workout.dict())
        return {"success": True, "workout_id": workout_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save workout: {str(e)}")


@app.get("/api/crossfit/workouts")
def get_crossfit_workouts(limit: int = Field(default=10, ge=1, le=100)):
    """Get recent CrossFit workouts"""
    df = db.get_crossfit_workouts(limit=limit)

    if df.empty:
        return []

    workouts = []
    for _, row in df.iterrows():
        workouts.append({
            "id": int(row['id']),
            "wod_name": row['wod_name'],
            "date": row['date'],
            "time": row['time'],
            "rounds": int(row['rounds']) if pd.notna(row['rounds']) else None,
            "reps": int(row['reps']) if pd.notna(row['reps']) else None,
            "weight": float(row['weight']) if pd.notna(row['weight']) else None,
            "rpe": int(row['rpe']) if pd.notna(row['rpe']) else None,
            "notes": row['notes']
        })

    return workouts


# ========== STRAVA INTEGRATION ==========

@app.post("/api/strava/sync")
def sync_strava(days: int = Field(default=30, ge=1, le=365)):
    """Sync activities from Strava"""
    try:
        count = strava_collector.sync_to_database(db, days)
        return {
            "success": True,
            "synced_activities": count,
            "days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@app.get("/api/strava/stats")
def get_strava_stats():
    """Get Strava connection status — does not expose credentials"""
    return {
        "connected": strava_collector.access_token is not None,
    }


@app.post("/api/activities/sync")
def sync_single_activity(activity: Activity):
    """Sync a single activity (for external sync scripts)"""
    try:
        # Convert to DataFrame format for database
        activity_dict = activity.dict()
        activity_dict['id'] = activity_dict.get('id') or int(datetime.now().timestamp())
        
        df = pd.DataFrame([activity_dict])
        db.save_activities(df)
        
        return {
            "success": True,
            "message": f"Activity '{activity.name}' synced successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ========== APPLE HEALTH (Health Auto Export) ==========

@app.post("/api/apple-health/webhook")
def apple_health_webhook(data: HealthAutoExportData):
    """
    Receive data from Health Auto Export app

    Configure the app to POST to:
    http://your-server:8000/api/apple-health/webhook

    Requires X-API-Key header when BIOMONITOR_API_KEY env var is set.
    """
    try:
        # Save the webhook data to disk
        filepath = apple_collector.save_webhook_data(data.dict())

        # Parse metrics
        metrics = apple_collector.parse_health_export(filepath)

        # Save each metric record to the database
        saved_count = 0
        for metric_type, records in metrics.items():
            for record in records:
                db.save_health_metric({
                    'date': record.get('date'),
                    'metric_type': record.get('type', metric_type),
                    'value': record.get('value'),
                    'unit': record.get('unit', ''),
                    'source': 'apple_health',
                })
                saved_count += 1

        return {
            "success": True,
            "records_processed": saved_count,
            "metrics_types": list(metrics.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@app.get("/api/health-metrics/latest")
def get_latest_health_metrics():
    """Get latest health metrics from Apple Health database"""
    return db.get_latest_health_metrics()


@app.get("/api/health-metrics/history")
def get_health_metrics_history(
    days: int = Field(default=30, ge=1, le=365),
    metric_type: Optional[str] = None
):
    """Get health metrics history for charts"""
    return db.get_health_metrics_history(days=days, metric_type=metric_type)


@app.get("/api/apple-health/formats")
def get_apple_health_formats():
    """Return Apple Watch / Health Auto Export metric format examples."""
    return {
        "source": "Health Auto Export",
        "supported_metrics": [
            {"name": "Heart Rate", "healthkit_type": "HKQuantityTypeIdentifierHeartRate", "unit": "count/min",
             "sample": {"type": "HeartRate", "date": "2026-03-15T07:32:00+08:00", "value": 128, "unit": "count/min", "source": "Apple Watch Series 9"}},
            {"name": "HRV", "healthkit_type": "HKQuantityTypeIdentifierHeartRateVariabilitySDNN", "unit": "ms",
             "sample": {"type": "HeartRateVariabilitySDNN", "date": "2026-03-15T06:45:00+08:00", "value": 49, "unit": "ms"}},
            {"name": "Sleep Analysis", "healthkit_type": "HKCategoryTypeIdentifierSleepAnalysis", "unit": "state",
             "sample": {"type": "SleepAnalysis", "date": "2026-03-15T00:10:00+08:00", "value": "asleepCore", "duration_minutes": 432}},
            {"name": "Active Energy", "healthkit_type": "HKQuantityTypeIdentifierActiveEnergyBurned", "unit": "kcal",
             "sample": {"type": "ActiveEnergyBurned", "date": "2026-03-15T18:10:00+08:00", "value": 684, "unit": "kcal"}},
            {"name": "Blood Oxygen", "healthkit_type": "HKQuantityTypeIdentifierOxygenSaturation", "unit": "%",
             "sample": {"type": "OxygenSaturation", "date": "2026-03-15T08:05:00+08:00", "value": 98, "unit": "%"}},
            {"name": "Wrist Temperature", "healthkit_type": "HKQuantityTypeIdentifierAppleSleepingWristTemperature", "unit": "deg C delta",
             "sample": {"type": "AppleSleepingWristTemperature", "date": "2026-03-15T06:30:00+08:00", "value": 0.2, "unit": "deg C delta"}},
        ]
    }


# ========== OURA RING (Carl) ==========

@app.post("/api/oura/sync")
def sync_oura(days: int = Field(default=7, ge=1, le=90)):
    """Sync Oura Ring data for Carl"""
    try:
        counts = oura_collector.sync_to_database(db, days)
        if "skipped" in counts:
            raise HTTPException(status_code=503, detail=counts["skipped"])
        return {
            "success": True,
            "days": days,
            "synced": counts,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Oura sync failed: {str(exc)}")


@app.get("/api/oura/readiness")
def get_oura_readiness(days: int = Field(default=7, ge=1, le=90)):
    """Get Oura readiness scores from the database"""
    records = db.get_health_metrics_history(days=days, metric_type="OuraReadiness")
    return {
        "days": days,
        "metric_type": "OuraReadiness",
        "data": records,
    }


@app.get("/api/oura/sleep")
def get_oura_sleep(days: int = Field(default=7, ge=1, le=90)):
    """Get Oura sleep data from the database (score + duration)"""
    scores = db.get_health_metrics_history(days=days, metric_type="OuraSleepScore")
    durations = db.get_health_metrics_history(days=days, metric_type="OuraSleepDuration")
    return {
        "days": days,
        "scores": scores,
        "durations": durations,
    }


# ========== XIAOMI MI BAND (Zelda) ==========

@app.post("/api/xiaomi/upload")
async def upload_xiaomi_export(file_content: XiaomiExportData):
    """
    Accept Mi Fitness or Gadgetbridge export data.

    Send a JSON body with:
    - format: "gadgetbridge" or "mi_fitness"
    - data: array of record objects

    The payload is saved to disk and all recognised metrics are written to
    the health_metrics table.
    """
    try:
        import tempfile, json as _json

        fmt = file_content.format.lower().strip()
        if fmt not in ("gadgetbridge", "mi_fitness"):
            raise HTTPException(
                status_code=400,
                detail=f"Unknown format '{fmt}'. Use 'gadgetbridge' or 'mi_fitness'.",
            )

        # Write the records to a temp file so the collector can parse them
        suffix = ".csv" if fmt == "mi_fitness" else ".json"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, encoding="utf-8"
        ) as tmp:
            if fmt == "mi_fitness":
                import csv as _csv, io as _io
                if file_content.data:
                    fieldnames = list(file_content.data[0].keys())
                    out = _io.StringIO()
                    writer = _csv.DictWriter(out, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(file_content.data)
                    tmp.write(out.getvalue())
            else:
                _json.dump(file_content.data, tmp)
            tmp_path = tmp.name

        saved = xiaomi_collector.sync_to_database(db, tmp_path)

        import os as _os
        try:
            _os.unlink(tmp_path)
        except OSError:
            pass

        total = sum(saved.values())
        return {
            "success": True,
            "format": fmt,
            "records_saved": total,
            "breakdown": saved,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(exc)}")


@app.post("/api/xiaomi/webhook")
def xiaomi_gadgetbridge_webhook(data: XiaomiWebhookData):
    """
    Receive real-time data from the Gadgetbridge HTTP server plugin.

    Configure Gadgetbridge:
      Settings -> HTTP server -> Enable
      URL: http://YOUR_SERVER_IP:8000/api/xiaomi/webhook
    """
    try:
        payload = data.dict(exclude_none=False)

        # Persist raw payload for replay / audit
        xiaomi_collector.save_gadgetbridge_webhook(payload)

        # Parse and save to DB
        metrics = xiaomi_collector.parse_gadgetbridge_webhook(payload)

        saved_count = 0
        for category, records in metrics.items():
            for record in records:
                db.save_health_metric(
                    {
                        "date": record.get("date"),
                        "metric_type": record.get("type", category),
                        "value": record.get("value"),
                        "unit": record.get("unit", ""),
                        "source": "xiaomi_band",
                    }
                )
                saved_count += 1

        return {
            "success": True,
            "records_saved": saved_count,
            "battery": data.battery,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(exc)}")


@app.get("/api/xiaomi/stats")
def get_xiaomi_stats(days: int = Field(default=7, ge=1, le=90)):
    """Get Xiaomi Mi Band metrics from the database."""
    metric_types = [
        "StepCount",
        "HeartRate",
        "SleepAnalysis",
        "ActiveEnergyBurned",
    ]

    result: Dict[str, Any] = {"days": days, "source": "xiaomi_band"}
    for mt in metric_types:
        history = db.get_health_metrics_history(days=days, metric_type=mt)
        # Filter to xiaomi_band source only when possible
        xiaomi_records = [
            r for r in history
            if isinstance(r, dict) and r.get("source") == "xiaomi_band"
        ] or history  # fall back to all sources if source field not stored
        result[mt] = xiaomi_records

    return result


@app.get("/api/share/card")
def generate_share_card():
    """Generate data for share card"""
    stats = get_current_week_stats()
    health = get_latest_health_metrics()

    return {
        "week": stats['week_start'],
        "crossfit": {
            "completed": stats['crossfit_sessions'],
            "target": 3
        },
        "walking": {
            "distance_km": stats['walking_distance_km']
        },
        "hrv": health.get('hrv'),
        "resting_hr": health.get('resting_hr')
    }


# ========== WHOOP (ZN) ==========


class WhoopCallbackRequest(BaseModel):
    code: str


@app.get("/api/whoop/auth-url")
def get_whoop_auth_url():
    """Return the OAuth 2.0 authorization URL for ZN to connect WHOOP.

    The user visits this URL in a browser, authorizes BioMonitor, and is
    redirected to /api/whoop/callback with an authorization code.

    Example:
        https://api.prod.whoop.com/oauth/oauth2/auth?client_id=...
        &redirect_uri=http://localhost:8000/api/whoop/callback
        &scope=read:recovery%20read:sleep%20read:workout%20read:cycles%20read:body_measurement
        &response_type=code
    """
    if not whoop_collector.client_id:
        raise HTTPException(
            status_code=503,
            detail=(
                "WHOOP client_id is not configured. "
                "Add whoop.client_id and whoop.client_secret to config.yaml."
            ),
        )
    return {"auth_url": whoop_collector.get_authorization_url()}


@app.post("/api/whoop/callback")
def whoop_oauth_callback(body: WhoopCallbackRequest):
    """Exchange an OAuth authorization code for WHOOP access + refresh tokens.

    After authorizing in the browser, copy the 'code' query parameter from
    the redirect URL and POST it here:

        curl -X POST http://localhost:8000/api/whoop/callback \\
             -H 'Content-Type: application/json' \\
             -d '{"code": "YOUR_CODE_HERE"}'

    Tokens are persisted to config.yaml automatically.
    """
    success = whoop_collector.exchange_code_for_tokens(body.code)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Token exchange failed. Check your client_id, client_secret, and that the code has not expired.",
        )
    return {"success": True, "message": "WHOOP tokens saved. You can now sync data."}


@app.post("/api/whoop/sync")
def sync_whoop(days: int = Field(default=7, ge=1, le=90)):
    """Sync WHOOP data for ZN (recovery, sleep, strain).

    Fetches the last *days* of WHOOP data and saves it to the health_metrics
    table. The access token is refreshed automatically if it has expired.

    Returns a dict of metric_type -> count of records saved.
    """
    try:
        counts = whoop_collector.sync_to_database(db, days)
        return {"success": True, "days": days, "saved": counts}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"WHOOP sync failed: {str(exc)}")


@app.get("/api/whoop/recovery")
def get_whoop_recovery(days: int = Field(default=7, ge=1, le=90)):
    """Get WHOOP recovery scores from the database.

    Returns records of metric_type='WhoopRecovery' for the last *days* days.
    """
    return db.get_health_metrics_history(days=days, metric_type="WhoopRecovery")


@app.get("/api/whoop/strain")
def get_whoop_strain(days: int = Field(default=7, ge=1, le=90)):
    """Get WHOOP strain scores from the database.

    Returns records of metric_type='WhoopStrain' for the last *days* days.
    """
    return db.get_health_metrics_history(days=days, metric_type="WhoopStrain")


# ========== SMART REMINDERS ==========
from engine import RemindersEngine


@app.get("/api/reminders/sleep")
def get_sleep_recommendation():
    """Analyse recent sleep data and return a bedtime / wake-time recommendation."""
    engine = RemindersEngine(db)
    return engine.sleep_recommendation()


@app.get("/api/reminders/hydration")
def get_hydration_schedule(
    wake_time: str = "07:00",
    sleep_time: str = "23:00",
):
    """Generate an hourly water-intake schedule for today."""
    engine = RemindersEngine(db)
    return engine.hydration_schedule(wake_time=wake_time, sleep_time=sleep_time)


@app.get("/api/reminders/standing")
def get_standing_reminders(
    work_start: str = "09:00",
    work_end: str = "18:00",
):
    """Generate stand-up reminders during work hours (every 50 min of sitting)."""
    engine = RemindersEngine(db)
    return engine.standing_reminders(work_start=work_start, work_end=work_end)


@app.get("/api/reminders/fitness")
def get_fitness_reminders(weekly_target: int = Field(default=3, ge=1, le=7)):
    """Smart workout scheduling based on this week's CrossFit count and HRV."""
    engine = RemindersEngine(db)
    return engine.fitness_reminders(weekly_target=weekly_target)


@app.get("/api/reminders/recovery")
def get_recovery_recommendation():
    """Score recovery 0-100 from WHOOP, Oura, and HRV data."""
    engine = RemindersEngine(db)
    return engine.rest_recommendation()


@app.get("/api/reminders/daily")
def get_daily_schedule(
    wake_time: str = "07:00",
    sleep_time: str = "23:00",
    work_start: str = "09:00",
    work_end: str = "18:00",
):
    """Merge all reminders into a single sorted daily timeline."""
    engine = RemindersEngine(db)
    return engine.daily_schedule(
        wake_time=wake_time,
        sleep_time=sleep_time,
        work_start=work_start,
        work_end=work_end,
    )


# ========== SUPPLEMENTS & USER PROFILES ==========

_supplement_engine = SupplementEngine()
_KNOWN_USERS = ["carl", "zelda", "zn", "default"]


def _get_health_metrics_for_profile(profile: UserProfile) -> Dict[str, Any]:
    """
    Pull recent health metrics from the DB and compute averages that can
    enrich a UserProfile before supplement recommendations are generated.
    """
    metrics: Dict[str, Any] = {}

    try:
        # HRV
        hrv_records = db.get_health_metrics_history(days=30, metric_type="HeartRateVariabilitySDNN")
        if hrv_records:
            vals = [r["value"] for r in hrv_records if isinstance(r.get("value"), (int, float))]
            if vals:
                metrics["avg_hrv"] = round(sum(vals) / len(vals), 1)

        # Resting HR
        hr_records = db.get_health_metrics_history(days=30, metric_type="HeartRate")
        if hr_records:
            vals = [r["value"] for r in hr_records if isinstance(r.get("value"), (int, float))]
            if vals:
                metrics["avg_resting_hr"] = round(sum(vals) / len(vals), 1)

        # Sleep (Oura)
        sleep_records = db.get_health_metrics_history(days=30, metric_type="OuraSleepDuration")
        if sleep_records:
            vals = [r["value"] for r in sleep_records if isinstance(r.get("value"), (int, float))]
            if vals:
                # OuraSleepDuration is stored in seconds
                metrics["avg_sleep_hours"] = round((sum(vals) / len(vals)) / 3600, 1)

        # WHOOP recovery
        whoop_recovery = db.get_health_metrics_history(days=30, metric_type="WhoopRecovery")
        if whoop_recovery:
            vals = [r["value"] for r in whoop_recovery if isinstance(r.get("value"), (int, float))]
            if vals:
                metrics["recovery_score"] = round(sum(vals) / len(vals), 1)

        # Oura readiness as fallback recovery score
        if "recovery_score" not in metrics:
            oura_ready = db.get_health_metrics_history(days=30, metric_type="OuraReadiness")
            if oura_ready:
                vals = [r["value"] for r in oura_ready if isinstance(r.get("value"), (int, float))]
                if vals:
                    metrics["recovery_score"] = round(sum(vals) / len(vals), 1)
    except Exception:
        # Never let metric-fetching failures block supplement recommendations
        pass

    return metrics


@app.get("/api/users/{user_id}/profile")
def get_user_profile(user_id: str):
    """Return the YAML-backed profile for a user."""
    profile = load_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Profile not found for user '{user_id}'")
    from dataclasses import asdict
    return asdict(profile)


@app.put("/api/users/{user_id}/profile")
def update_user_profile(user_id: str, updates: Dict[str, Any]):
    """Merge partial updates into a user's profile and persist."""
    profile = load_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Profile not found for user '{user_id}'")

    from dataclasses import asdict, replace
    current = asdict(profile)
    # Only allow updating known fields; ignore unknown keys
    allowed_fields = set(current.keys())
    safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    if not safe_updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    updated_profile = replace(profile, **safe_updates)
    save_profile(updated_profile)
    return asdict(updated_profile)


@app.get("/api/users/{user_id}/supplements")
def get_supplement_recommendations(user_id: str):
    """Return a flat list of personalised supplement recommendations."""
    profile = load_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Profile not found for user '{user_id}'")

    health_metrics = _get_health_metrics_for_profile(profile)
    supplements = _supplement_engine.recommend(profile, health_metrics)
    return {
        "user_id": user_id,
        "name": profile.name,
        "supplements": [s.to_dict() for s in supplements],
        "count": len(supplements),
    }


@app.get("/api/users/{user_id}/supplements/daily-plan")
def get_daily_supplement_plan(user_id: str):
    """Return supplements grouped by timing for a daily schedule view."""
    profile = load_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Profile not found for user '{user_id}'")

    health_metrics = _get_health_metrics_for_profile(profile)
    supplements = _supplement_engine.recommend(profile, health_metrics)
    plan = _supplement_engine.as_daily_plan(supplements)
    return {
        "user_id": user_id,
        "name": profile.name,
        "device": profile.device,
        "health_goals": profile.health_goals,
        "recovery_score": profile.recovery_score,
        "avg_sleep_hours": profile.avg_sleep_hours,
        "avg_hrv": profile.avg_hrv,
        "plan": plan,
    }


@app.get("/api/supplements/all-users")
def get_all_users_supplements():
    """Return supplement recommendations for all known users side by side."""
    result: Dict[str, Any] = {}
    for uid in _KNOWN_USERS:
        profile = load_profile(uid)
        if profile is None:
            result[uid] = {"error": "profile not found"}
            continue
        health_metrics = _get_health_metrics_for_profile(profile)
        supplements = _supplement_engine.recommend(profile, health_metrics)
        plan = _supplement_engine.as_daily_plan(supplements)
        result[uid] = {
            "name": profile.name,
            "device": profile.device,
            "health_goals": profile.health_goals,
            "plan": plan,
        }
    return result


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("BIOMONITOR_HOST", "127.0.0.1")
    port = int(os.environ.get("BIOMONITOR_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
