#!/usr/bin/env python3
"""Setup demo data for BioMonitor presentation"""

import sqlite3
from datetime import datetime, timedelta
import os

print("🚀 Setting up BioMonitor demo data...")

# Initialize database
conn = sqlite3.connect('biomonitor.db')
cursor = conn.cursor()

# Create tables
cursor.executescript('''
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY,
    name TEXT,
    type TEXT,
    start_date TEXT,
    distance REAL,
    moving_time INTEGER,
    average_heartrate REAL,
    max_heartrate REAL,
    is_crossfit BOOLEAN,
    is_walking BOOLEAN
);

CREATE TABLE IF NOT EXISTS crossfit_workouts (
    id INTEGER PRIMARY KEY,
    wod_name TEXT,
    date TEXT,
    time TEXT,
    rounds INTEGER,
    reps INTEGER,
    weight REAL,
    rpe INTEGER,
    notes TEXT
);
''')

# Add demo activities
now = datetime.now()
activities = [
    (1, "CrossFit WOD: Fran", "Workout", (now - timedelta(days=1)).isoformat(), 0, 420, 165, 185, 1, 0),
    (2, "Morning Walk", "Walk", (now - timedelta(days=1)).isoformat(), 2.5, 1800, 110, 130, 0, 1),
    (3, "CrossFit WOD: Grace", "Workout", (now - timedelta(days=3)).isoformat(), 0, 180, 160, 175, 1, 0),
    (4, "Evening Walk", "Walk", (now - timedelta(days=2)).isoformat(), 3.2, 2400, 105, 120, 0, 1),
    (5, "CrossFit WOD: Murph", "Workout", (now - timedelta(days=5)).isoformat(), 0, 2400, 155, 170, 1, 0),
    (6, "Lunch Walk", "Walk", (now - timedelta(days=4)).isoformat(), 1.8, 1200, 100, 115, 0, 1),
]

for a in activities:
    cursor.execute(
        '''
        INSERT OR REPLACE INTO activities (
            id, name, type, start_date, distance, moving_time,
            average_heartrate, max_heartrate, is_crossfit, is_walking
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        a
    )

# Add CrossFit workouts
crossfit = [
    (1, "Fran", (now - timedelta(days=1)).strftime("%Y-%m-%d"), "4:52", None, None, None, 8, "Thrusters + Pull-ups"),
    (2, "Grace", (now - timedelta(days=3)).strftime("%Y-%m-%d"), "3:15", None, None, 135, 9, "30 Clean & Jerks"),
    (3, "Murph", (now - timedelta(days=5)).strftime("%Y-%m-%d"), "42:30", None, None, 20, 7, "With 20lb vest"),
]

for c in crossfit:
    cursor.execute(
        '''
        INSERT OR REPLACE INTO crossfit_workouts (
            id, wod_name, date, time, rounds, reps, weight, rpe, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        c
    )

conn.commit()
conn.close()

print("✅ Demo data ready!")
print(f"   • {len([a for a in activities if a[8]])} CrossFit sessions")
print(f"   • {len([a for a in activities if a[9]])} Walking activities")
print(f"   • {len(crossfit)} WOD records")
print("\n🎯 Ready to demo! Start the servers:")
print("   python api_server.py")
print("   cd dashboard/web && npm run dev")
