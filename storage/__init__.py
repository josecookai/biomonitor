"""
BioMonitor - Database Layer
SQLite storage for health and fitness data
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd


class BioDatabase:
    """SQLite database for BioMonitor"""

    def __init__(self, db_path: str = "biomonitor.db"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Activities table (from Strava)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY,
                strava_id BIGINT UNIQUE,
                name TEXT,
                type TEXT,
                sport_type TEXT,
                start_date TIMESTAMP,
                distance REAL,
                moving_time INTEGER,
                elapsed_time INTEGER,
                average_speed REAL,
                max_speed REAL,
                average_heartrate REAL,
                max_heartrate REAL,
                total_elevation_gain REAL,
                is_crossfit BOOLEAN,
                is_walking BOOLEAN,
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # CrossFit workouts (manual logging)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crossfit_workouts (
                id INTEGER PRIMARY KEY,
                date TIMESTAMP,
                wod_name TEXT,
                time TEXT,
                rounds INTEGER,
                reps INTEGER,
                weight REAL,
                rpe INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Health metrics (from Apple Watch)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_metrics (
                id INTEGER PRIMARY KEY,
                date TIMESTAMP,
                metric_type TEXT,
                value REAL,
                unit TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Daily summaries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summaries (
                date DATE PRIMARY KEY,
                crossfit_sessions INTEGER DEFAULT 0,
                walking_distance_km REAL DEFAULT 0,
                walking_time_min INTEGER DEFAULT 0,
                resting_hr REAL,
                hrv REAL,
                sleep_hours REAL,
                training_load REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # User settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def save_activity(self, activity: Dict) -> bool:
        """Save activity to database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO activities (
                    strava_id, name, type, sport_type, start_date,
                    distance, moving_time, elapsed_time, average_speed, max_speed,
                    average_heartrate, max_heartrate, total_elevation_gain,
                    is_crossfit, is_walking, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity.get('id'),
                activity.get('name'),
                activity.get('type'),
                activity.get('sport_type'),
                activity.get('start_date'),
                activity.get('distance'),
                activity.get('moving_time'),
                activity.get('elapsed_time'),
                activity.get('average_speed'),
                activity.get('max_speed'),
                activity.get('average_heartrate'),
                activity.get('max_heartrate'),
                activity.get('total_elevation_gain'),
                activity.get('is_crossfit'),
                activity.get('is_walking'),
                json.dumps(activity)
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving activity: {e}")
            return False
        finally:
            conn.close()

    def save_crossfit_workout(self, workout: Dict) -> int:
        """Save CrossFit workout to database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO crossfit_workouts (date, wod_name, time, rounds, reps, weight, rpe, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                workout.get('date'),
                workout.get('wod_name'),
                workout.get('time'),
                workout.get('rounds'),
                workout.get('reps'),
                workout.get('weight'),
                workout.get('rpe'),
                workout.get('notes')
            ))
            workout_id = cursor.lastrowid
            conn.commit()
            return workout_id
        except Exception as e:
            print(f"Error saving crossfit workout: {e}")
            raise
        finally:
            conn.close()

    def save_health_metric(self, metric: Dict) -> bool:
        """Save a single health metric to database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO health_metrics (date, metric_type, value, unit, source)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                metric.get('date'),
                metric.get('metric_type'),
                metric.get('value'),
                metric.get('unit', ''),
                metric.get('source', 'apple_health')
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving health metric: {e}")
            return False
        finally:
            conn.close()

    def get_latest_health_metrics(self) -> Dict:
        """Get the most recent value for each key health metric type"""
        conn = self.get_connection()
        cursor = conn.cursor()

        result: Dict = {}
        metric_map = {
            'HeartRate': 'resting_hr',
            'HeartRateVariability': 'hrv',
            'SleepAnalysis': 'sleep_hours',
            'StepCount': 'steps',
        }

        for metric_type, field_name in metric_map.items():
            cursor.execute(
                "SELECT value FROM health_metrics WHERE metric_type = ? ORDER BY date DESC LIMIT 1",
                (metric_type,)
            )
            row = cursor.fetchone()
            if row:
                result[field_name] = row['value']

        conn.close()
        result['source'] = 'apple_health'
        return result

    def get_health_metrics_history(self, days: int = 30, metric_type: Optional[str] = None) -> List[Dict]:
        """Get health metrics history as a list"""
        conn = self.get_connection()
        cursor = conn.cursor()

        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        if metric_type:
            cursor.execute(
                "SELECT date, metric_type, value, unit FROM health_metrics "
                "WHERE date >= ? AND metric_type = ? ORDER BY date ASC",
                (cutoff, metric_type)
            )
        else:
            cursor.execute(
                "SELECT date, metric_type, value, unit FROM health_metrics "
                "WHERE date >= ? ORDER BY date ASC",
                (cutoff,)
            )

        rows = cursor.fetchall()
        conn.close()

        return [
            {"date": row["date"], "metric_type": row["metric_type"], "value": row["value"], "unit": row["unit"]}
            for row in rows
        ]

    def get_activities(self, start_date: datetime = None, end_date: datetime = None, limit: int = 1000) -> pd.DataFrame:
        """Get activities as DataFrame"""
        conn = self.get_connection()

        query = "SELECT * FROM activities WHERE 1=1"
        params: list = []

        if start_date:
            query += " AND start_date >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND start_date <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY start_date DESC LIMIT ?"
        params.append(limit)

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        return df

    def get_crossfit_workouts(self, start_date: datetime = None, end_date: datetime = None, limit: int = 100) -> pd.DataFrame:
        """Get CrossFit workouts as DataFrame"""
        conn = self.get_connection()

        query = "SELECT * FROM crossfit_workouts WHERE 1=1"
        params: list = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND date <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        return df

    def get_weekly_summary(self, year: int = None, week: int = None) -> Dict:
        """Get summary for a specific week"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if year is None or week is None:
            now = datetime.now()
            year = now.isocalendar()[0]
            week = now.isocalendar()[1]

        # Build week boundaries from ISO week
        import datetime as dt
        week_start = dt.datetime.fromisocalendar(year, week, 1).isoformat()
        week_end = dt.datetime.fromisocalendar(year, week, 7).replace(hour=23, minute=59, second=59).isoformat()

        cursor.execute(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN is_crossfit = 1 THEN 1 ELSE 0 END) as crossfit_count, "
            "SUM(CASE WHEN is_walking = 1 THEN distance ELSE 0 END) / 1000 as walking_km "
            "FROM activities WHERE start_date BETWEEN ? AND ?",
            (week_start, week_end)
        )
        row = cursor.fetchone()
        conn.close()

        return {
            'year': year,
            'week': week,
            'total_activities': row['total'] or 0,
            'crossfit_sessions': row['crossfit_count'] or 0,
            'walking_distance_km': round(row['walking_km'] or 0, 2),
        }

    def set_setting(self, key: str, value: str):
        """Save setting"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))

        conn.commit()
        conn.close()

    def get_setting(self, key: str, default=None) -> Optional[str]:
        """Get setting value"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()

        return row['value'] if row else default


# Export
__all__ = ['BioDatabase']
