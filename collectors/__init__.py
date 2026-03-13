"""
BioMonitor - Data Collectors
Collect health and fitness data from multiple sources
"""

import os
import json
import sqlite3
import yaml
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
import pandas as pd


def load_config():
    """Load configuration from config.yaml"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


class StravaCollector:
    """Collect workout data from Strava API"""
    
    def __init__(self, access_token: str = None):
        config = load_config()
        strava_config = config.get('strava', {})
        
        self.access_token = access_token or strava_config.get('access_token')
        self.client_id = strava_config.get('client_id')
        self.client_secret = strava_config.get('client_secret')
        self.refresh_token = strava_config.get('refresh_token')
        self.base_url = "https://www.strava.com/api/v3"
    
    def refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            return False
        
        response = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access_token']
            self.refresh_token = data.get('refresh_token', self.refresh_token)
            return True
        return False
    
    def get_activities(self, after: datetime = None, per_page: int = 30) -> List[Dict]:
        """Fetch recent activities from Strava"""
        if after is None:
            after = datetime.now() - timedelta(days=30)
        
        after_timestamp = int(after.timestamp())
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {
            "after": after_timestamp,
            "per_page": per_page
        }
        
        response = requests.get(
            f"{self.base_url}/athlete/activities",
            headers=headers,
            params=params
        )
        
        if response.status_code == 401:
            # Token expired, try refresh
            if self.refresh_access_token():
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = requests.get(
                    f"{self.base_url}/athlete/activities",
                    headers=headers,
                    params=params
                )
        
        response.raise_for_status()
        return response.json()
    
    def identify_crossfit(self, activity: Dict) -> bool:
        """Identify if activity is CrossFit based on characteristics"""
        activity_type = activity.get('type', '')
        name = activity.get('name', '').lower()
        
        # Direct indicators
        if any(keyword in name for keyword in ['crossfit', 'wod', 'murph', 'fran', 'grace', 'helen']):
            return True
        
        # Workout characteristics (relaxed criteria)
        avg_hr = activity.get('average_heartrate', 0) or 0
        max_hr = activity.get('max_heartrate', 0) or 0
        duration = activity.get('moving_time', 0) / 60  # minutes
        
        # CrossFit patterns: high intensity workout, 20-90 min, elevated HR
        # Relaxed: avg HR > 130 OR max HR > 165
        if (activity_type == 'Workout' and 
            20 <= duration <= 120 and 
            (avg_hr > 130 or max_hr > 165)):
            return True
        
        return False
    
    def identify_walking(self, activity: Dict) -> bool:
        """Identify walking activities"""
        activity_type = activity.get('type', '')
        name = activity.get('name', '').lower()
        
        if activity_type == 'Walk':
            return True
        
        if 'walk' in name or 'stroll' in name:
            return True
        
        return False
    
    def process_activity(self, activity: Dict) -> Dict:
        """Process raw activity data"""
        return {
            'id': activity.get('id'),
            'name': activity.get('name'),
            'type': activity.get('type'),
            'sport_type': activity.get('sport_type'),
            'start_date': activity.get('start_date'),
            'distance': activity.get('distance', 0),  # meters
            'moving_time': activity.get('moving_time', 0),  # seconds
            'elapsed_time': activity.get('elapsed_time', 0),
            'average_speed': activity.get('average_speed', 0),
            'max_speed': activity.get('max_speed', 0),
            'average_heartrate': activity.get('average_heartrate'),
            'max_heartrate': activity.get('max_heartrate'),
            'total_elevation_gain': activity.get('total_elevation_gain', 0),
            'calories': activity.get('calories'),
            'is_crossfit': self.identify_crossfit(activity),
            'is_walking': self.identify_walking(activity),
            'source': 'strava'
        }
    
    def sync_to_database(self, db, days: int = 30) -> int:
        """Sync Strava activities to database"""
        after = datetime.now() - timedelta(days=days)
        activities = self.get_activities(after)
        
        count = 0
        for activity in activities:
            processed = self.process_activity(activity)
            if db.save_activity(processed):
                count += 1
        
        return count


class AppleHealthCollector:
    """Collect health data from Apple Health exports and webhooks"""
    
    def __init__(self, export_path: str = None):
        config = load_config()
        health_config = config.get('apple_health', {})
        self.export_path = export_path or health_config.get('export_path', '/tmp/apple_health_exports')
        os.makedirs(self.export_path, exist_ok=True)
    
    def save_webhook_data(self, data: Dict) -> str:
        """Save data from Health Auto Export webhook"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"health_export_{timestamp}.json"
        filepath = os.path.join(self.export_path, filename)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filepath
    
    def parse_health_export(self, filepath: str) -> Dict:
        """Parse Health Auto Export JSON data"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Extract metrics
        metrics = {
            'heart_rate': [],
            'hrv': [],
            'sleep': [],
            'steps': [],
            'active_energy': []
        }
        
        # Parse based on Health Auto Export format
        if 'data' in data:
            for record in data['data']:
                metric_type = record.get('type', '')
                value = record.get('value', 0)
                date = record.get('date', '')
                
                if 'HeartRate' in metric_type:
                    metrics['heart_rate'].append({'date': date, 'value': value})
                elif 'HeartRateVariability' in metric_type:
                    metrics['hrv'].append({'date': date, 'value': value})
                elif 'SleepAnalysis' in metric_type:
                    metrics['sleep'].append({'date': date, 'value': value})
                elif 'StepCount' in metric_type:
                    metrics['steps'].append({'date': date, 'value': value})
        
        return metrics


class CrossFitLogger:
    """Manual CrossFit workout logger"""
    
    def __init__(self, db_path: str = "biomonitor.db"):
        self.db_path = db_path
    
    def log_wod(self, 
                wod_name: str,
                date: datetime = None,
                time: str = None,
                rounds: int = None,
                reps: int = None,
                weight: float = None,
                rpe: int = None,
                notes: str = None) -> int:
        """Log a CrossFit workout"""
        
        if date is None:
            date = datetime.now()
        
        workout = {
            'date': date.isoformat(),
            'wod_name': wod_name,
            'time': time,
            'rounds': rounds,
            'reps': reps,
            'weight': weight,
            'rpe': rpe,
            'notes': notes,
            'source': 'manual'
        }
        
        # TODO: Save to database
        return 1
    
    def get_weekly_count(self, year: int = None, week: int = None) -> int:
        """Get number of CrossFit sessions in a week"""
        # TODO: Query database
        pass


# Export all collectors
__all__ = ['StravaCollector', 'AppleHealthCollector', 'CrossFitLogger', 'load_config']
