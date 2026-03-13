"""
BioMonitor - Data Collectors
Collect health and fitness data from multiple sources
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
import pandas as pd


class StravaCollector:
    """Collect workout data from Strava API"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://www.strava.com/api/v3"
    
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
        response.raise_for_status()
        
        return response.json()
    
    def identify_crossfit(self, activity: Dict) -> bool:
        """Identify if activity is CrossFit based on characteristics"""
        activity_type = activity.get('type', '')
        name = activity.get('name', '').lower()
        
        # Direct indicators
        if 'crossfit' in name or 'wod' in name:
            return True
        
        # Workout characteristics
        avg_hr = activity.get('average_heartrate', 0)
        max_hr = activity.get('max_heartrate', 0)
        duration = activity.get('moving_time', 0) / 60  # minutes
        
        # CrossFit patterns: high intensity, 20-60 min, high HR
        if (activity_type == 'Workout' and 
            15 <= duration <= 90 and 
            avg_hr > 140 and 
            max_hr > 170):
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
            'is_crossfit': self.identify_crossfit(activity),
            'is_walking': self.identify_walking(activity),
            'source': 'strava'
        }


class AppleHealthCollector:
    """Collect health data from Apple Health exports"""
    
    def __init__(self, export_path: str):
        self.export_path = export_path
    
    def parse_export(self) -> pd.DataFrame:
        """Parse Apple Health export.xml file"""
        # TODO: Implement XML parsing
        pass
    
    def get_heart_rate_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get heart rate readings"""
        # TODO: Filter HR data by date range
        pass
    
    def get_hrv_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get HRV (Heart Rate Variability) data"""
        pass
    
    def get_sleep_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get sleep analysis data"""
        pass


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
__all__ = ['StravaCollector', 'AppleHealthCollector', 'CrossFitLogger']
