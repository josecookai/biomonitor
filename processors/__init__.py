"""
BioMonitor - Data Processors
Calculate metrics and analyze trends
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


class MetricsCalculator:
    """Calculate health and fitness metrics"""
    
    def __init__(self, activities_df: pd.DataFrame = None):
        self.activities = activities_df
    
    def weekly_crossfit_count(self, week_start: datetime = None) -> int:
        """Count CrossFit sessions in a week"""
        if week_start is None:
            week_start = datetime.now() - timedelta(days=7)
        
        week_end = week_start + timedelta(days=7)
        
        # Convert dates to timezone-naive for comparison
        dates = pd.to_datetime(self.activities['start_date']).dt.tz_localize(None)
        
        # Filter activities
        crossfit_activities = self.activities[
            (self.activities['is_crossfit'] == True) &
            (dates >= week_start.replace(tzinfo=None)) &
            (dates < week_end.replace(tzinfo=None))
        ]
        
        return len(crossfit_activities)
    
    def weekly_walking_stats(self, week_start: datetime = None) -> Dict:
        """Calculate walking statistics for the week"""
        if week_start is None:
            week_start = datetime.now() - timedelta(days=7)
        
        week_end = week_start + timedelta(days=7)
        
        # Convert dates to timezone-naive for comparison
        dates = pd.to_datetime(self.activities['start_date']).dt.tz_localize(None)
        
        walking_activities = self.activities[
            (self.activities['is_walking'] == True) &
            (dates >= week_start.replace(tzinfo=None)) &
            (dates < week_end.replace(tzinfo=None))
        ]
        
        total_distance = walking_activities['distance'].sum() / 1000  # km
        total_time = walking_activities['moving_time'].sum() / 60  # minutes
        
        return {
            'sessions': len(walking_activities),
            'total_distance_km': round(total_distance, 2),
            'total_time_min': round(total_time, 0),
            'avg_distance_km': round(total_distance / len(walking_activities), 2) if len(walking_activities) > 0 else 0
        }
    
    def training_load_distribution(self, days: int = 30) -> Dict:
        """Analyze training load over time"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        dates = pd.to_datetime(self.activities['start_date']).dt.tz_localize(None)
        
        recent_activities = self.activities[dates >= cutoff_date.replace(tzinfo=None)]
        
        # Calculate TRIMP-like score (Training Impulse)
        # TRIMP = duration_min * avg_hr_factor
        recent_activities = recent_activities.copy()
        recent_activities['trimp'] = (
            recent_activities['moving_time'] / 60 * 
            recent_activities['average_heartrate'].fillna(100) / 100
        )
        
        daily_load = recent_activities.groupby(
            dates.dt.date
        )['trimp'].sum()
        
        return {
            'daily_load': daily_load.to_dict(),
            'average_daily_load': round(daily_load.mean(), 1),
            'max_daily_load': round(daily_load.max(), 1),
            'total_load': round(daily_load.sum(), 0)
        }
    
    def recovery_metrics(self, hr_data: pd.DataFrame = None, sleep_data: pd.DataFrame = None) -> Dict:
        """Calculate recovery-related metrics"""
        metrics = {}
        
        if hr_data is not None and not hr_data.empty:
            # Resting heart rate (minimum in morning hours)
            morning_hr = hr_data[
                (hr_data['date'].dt.hour >= 4) & 
                (hr_data['date'].dt.hour <= 8)
            ]
            metrics['resting_hr'] = morning_hr['hr'].min() if not morning_hr.empty else None
            
            # Average HRV if available
            if 'hrv' in hr_data.columns:
                metrics['avg_hrv'] = hr_data['hrv'].mean()
                metrics['hrv_trend'] = self._calculate_trend(hr_data['hrv'])
        
        if sleep_data is not None and not sleep_data.empty:
            metrics['avg_sleep_hours'] = sleep_data['duration_hours'].mean()
            metrics['sleep_quality'] = sleep_data['quality'].mean() if 'quality' in sleep_data.columns else None
        
        return metrics
    
    def _calculate_trend(self, series: pd.Series) -> str:
        """Calculate trend direction"""
        if len(series) < 7:
            return "insufficient_data"
        
        recent = series.tail(7).mean()
        previous = series.tail(14).head(7).mean()
        
        diff = recent - previous
        pct_change = (diff / previous) * 100 if previous != 0 else 0
        
        if pct_change > 5:
            return "increasing"
        elif pct_change < -5:
            return "decreasing"
        else:
            return "stable"


class TrendAnalyzer:
    """Analyze long-term trends in health data"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def crossfit_consistency(self, weeks: int = 12) -> Dict:
        """Analyze CrossFit training consistency"""
        # TODO: Query database for weekly counts
        pass
    
    def walking_progression(self, weeks: int = 12) -> Dict:
        """Analyze walking volume progression"""
        pass
    
    def recovery_trends(self, days: int = 30) -> Dict:
        """Analyze recovery metrics trends"""
        pass
    
    def detect_anomalies(self, metric: str, threshold: float = 2.0) -> List[Dict]:
        """Detect anomalous readings"""
        pass


# Export
__all__ = ['MetricsCalculator', 'TrendAnalyzer']
