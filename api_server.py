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
from collectors import StravaCollector, AppleHealthCollector

app = FastAPI(
    title="BioMonitor API",
    description="Health metrics tracking API",
    version="0.1.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("BIOMONITOR_HOST", "127.0.0.1")
    port = int(os.environ.get("BIOMONITOR_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
