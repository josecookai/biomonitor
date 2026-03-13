import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

# Initialize database and collectors
db = BioDatabase()
strava_collector = StravaCollector()
apple_collector = AppleHealthCollector()

# Pydantic models
class Activity(BaseModel):
    id: int
    name: str
    type: str
    start_date: str
    distance: Optional[float]
    moving_time: int
    average_heartrate: Optional[float]
    max_heartrate: Optional[float]
    is_crossfit: bool
    is_walking: bool

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

# API Routes

@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/activities")
def get_activities(
    limit: int = 30,
    activity_type: Optional[str] = None
):
    """Get recent activities"""
    df = db.get_activities()
    
    if df.empty:
        return []
    
    if activity_type:
        if activity_type == "crossfit":
            df = df[df['is_crossfit'] == True]
        elif activity_type == "walking":
            df = df[df['is_walking'] == True]
    
    df = df.head(limit)
    
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
def get_weekly_stats(weeks: int = 4):
    """Get weekly aggregated stats"""
    df = db.get_activities()
    
    if df.empty:
        return []
    
    df['start_date'] = pd.to_datetime(df['start_date'])
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
def get_daily_data(days: int = 30):
    """Get daily aggregated data for charts"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    df = db.get_activities(start_date, end_date)
    
    if df.empty:
        return []
    
    df['start_date'] = pd.to_datetime(df['start_date'])
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
    workout_data = workout.dict()
    
    workout_id = db.save_crossfit_workout(workout_data)
    
    return {"success": True, "workout_id": workout_id}

@app.get("/api/crossfit/workouts")
def get_crossfit_workouts(limit: int = 10):
    """Get recent CrossFit workouts"""
    df = db.get_crossfit_workouts()
    
    if df.empty:
        return []
    
    df = df.head(limit)
    
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
def sync_strava(days: int = 30):
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
    """Get Strava connection status"""
    return {
        "connected": strava_collector.access_token is not None,
        "client_id": strava_collector.client_id,
        "last_sync": None  # TODO: Track last sync time
    }

# ========== APPLE HEALTH (Health Auto Export) ==========

@app.post("/api/apple-health/webhook")
def apple_health_webhook(data: HealthAutoExportData):
    """
    Receive data from Health Auto Export app
    
    Configure the app to POST to:
    http://your-server:8000/api/apple-health/webhook
    """
    try:
        # Save the webhook data
        filepath = apple_collector.save_webhook_data(data.dict())
        
        # Parse metrics
        metrics = apple_collector.parse_health_export(filepath)
        
        # Save to database (TODO: implement health metrics table)
        saved_count = 0
        for metric_type, records in metrics.items():
            for record in records:
                # TODO: Save to health_metrics table
                saved_count += 1
        
        return {
            "success": True,
            "saved_to": filepath,
            "records_processed": saved_count,
            "metrics_types": list(metrics.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

@app.get("/api/health-metrics/latest")
def get_latest_health_metrics():
    """Get latest health metrics from Apple Health"""
    # TODO: Query from database
    return {
        "resting_hr": 70,
        "hrv": 49,
        "sleep_hours": 7.2,
        "steps": 8500,
        "source": "apple_health"
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
        "hrv": health['hrv'],
        "resting_hr": health['resting_hr']
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
