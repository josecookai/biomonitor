"""
XiaomiBandCollector — Xiaomi Mi Band data ingestion.

Supports two ingestion paths:
1. File import: JSON exports from Gadgetbridge, or CSV exports from Mi Fitness app
2. Gadgetbridge HTTP server plugin webhook (real-time)
"""

import csv
import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Metric type constants
# ---------------------------------------------------------------------------
METRIC_STEPS = "StepCount"
METRIC_HEART_RATE = "HeartRate"
METRIC_SLEEP = "SleepAnalysis"
METRIC_CALORIES = "ActiveEnergyBurned"

# Mi Fitness CSV column names (lowercase, stripped)
_MI_FITNESS_COLUMNS = {
    "date": "date",
    "steps": "steps",
    "distance": "distance",
    "calories": "calories",
    "heart_rate": "heart_rate",
    "sleep_start": "sleep_start",
    "sleep_end": "sleep_end",
    "sleep_duration": "sleep_duration",
}


class XiaomiBandCollector:
    """
    Collector for Xiaomi Mi Band data.

    Supports two ingestion methods:
    1. File import: Parse JSON/CSV exports from Mi Fitness app or Gadgetbridge
    2. Gadgetbridge webhook: Receive real-time data from Gadgetbridge HTTP server plugin
    """

    def __init__(self, export_path: str = None) -> None:
        if export_path is None:
            export_path = "/tmp/xiaomi_exports"
        self.export_path = export_path
        os.makedirs(self.export_path, exist_ok=True)

    # ------------------------------------------------------------------
    # Gadgetbridge export (SQLite .db or JSON)
    # ------------------------------------------------------------------

    def parse_gadgetbridge_export(self, filepath: str) -> Dict[str, List]:
        """
        Parse a Gadgetbridge export file.

        Gadgetbridge can export either:
        - A SQLite database (.db) containing tables like MI_BAND_ACTIVITY_SAMPLE
        - A JSON file with an array of activity objects

        Returns a dict keyed by metric category, each value being a list of
        normalised record dicts ready for ``sync_to_database``.
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Export file not found: {filepath}")

        ext = os.path.splitext(filepath)[1].lower()
        if ext in (".db", ".sqlite", ".sqlite3"):
            return self._parse_gadgetbridge_sqlite(filepath)
        return self._parse_gadgetbridge_json(filepath)

    def _parse_gadgetbridge_sqlite(self, filepath: str) -> Dict[str, List]:
        """Read the MI_BAND_ACTIVITY_SAMPLE table from a Gadgetbridge SQLite export."""
        metrics: Dict[str, List] = {
            "heart_rate": [],
            "steps": [],
            "sleep": [],
            "calories": [],
        }

        conn = sqlite3.connect(filepath)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()

            # Discover available tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row["name"].upper() for row in cursor.fetchall()}

            if "MI_BAND_ACTIVITY_SAMPLE" in tables:
                cursor.execute(
                    "SELECT TIMESTAMP, RAW_INTENSITY, STEPS, RAW_KIND, "
                    "HEART_RATE FROM MI_BAND_ACTIVITY_SAMPLE"
                )
                for row in cursor.fetchall():
                    ts = row["TIMESTAMP"]
                    date_str = datetime.utcfromtimestamp(ts).isoformat() if ts else None

                    steps = row["STEPS"]
                    if steps and steps > 0:
                        metrics["steps"].append(
                            {
                                "date": date_str,
                                "value": int(steps),
                                "unit": "count",
                                "type": METRIC_STEPS,
                            }
                        )

                    hr = row["HEART_RATE"]
                    if hr and 0 < hr < 255:  # 255 = sentinel for "no reading"
                        metrics["heart_rate"].append(
                            {
                                "date": date_str,
                                "value": int(hr),
                                "unit": "count/min",
                                "type": METRIC_HEART_RATE,
                            }
                        )
        finally:
            conn.close()

        return metrics

    def _parse_gadgetbridge_json(self, filepath: str) -> Dict[str, List]:
        """Parse a Gadgetbridge JSON export (array of activity objects)."""
        with open(filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)

        # Accept either a bare list or {"data": [...]}
        if isinstance(raw, dict):
            records = raw.get("data", raw.get("records", []))
        elif isinstance(raw, list):
            records = raw
        else:
            records = []

        metrics: Dict[str, List] = {
            "heart_rate": [],
            "steps": [],
            "sleep": [],
            "calories": [],
        }

        for record in records:
            date_str = record.get("date") or record.get("timestamp")
            if isinstance(date_str, (int, float)):
                date_str = datetime.utcfromtimestamp(date_str).isoformat()

            steps = record.get("steps")
            if steps is not None and int(steps) > 0:
                metrics["steps"].append(
                    {
                        "date": date_str,
                        "value": int(steps),
                        "unit": "count",
                        "type": METRIC_STEPS,
                    }
                )

            hr = record.get("heart_rate") or record.get("heartRate")
            if hr is not None and int(hr) > 0:
                metrics["heart_rate"].append(
                    {
                        "date": date_str,
                        "value": int(hr),
                        "unit": "count/min",
                        "type": METRIC_HEART_RATE,
                    }
                )

            sleep_duration = record.get("sleep_duration") or record.get("sleepDuration")
            if sleep_duration is not None:
                metrics["sleep"].append(
                    {
                        "date": date_str,
                        "value": float(sleep_duration),
                        "unit": "min",
                        "type": METRIC_SLEEP,
                    }
                )

            calories = record.get("calories") or record.get("activeCalories")
            if calories is not None:
                metrics["calories"].append(
                    {
                        "date": date_str,
                        "value": float(calories),
                        "unit": "kcal",
                        "type": METRIC_CALORIES,
                    }
                )

        return metrics

    # ------------------------------------------------------------------
    # Mi Fitness CSV export
    # ------------------------------------------------------------------

    def parse_mi_fitness_export(self, filepath: str) -> Dict[str, List]:
        """
        Parse a Mi Fitness app CSV export.

        Expected columns (case-insensitive, extra columns are ignored):
            date, steps, distance, calories, heart_rate,
            sleep_start, sleep_end, sleep_duration
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Export file not found: {filepath}")

        metrics: Dict[str, List] = {
            "heart_rate": [],
            "steps": [],
            "sleep": [],
            "calories": [],
        }

        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            # Normalise header names
            if reader.fieldnames is None:
                return metrics

            normalised_fields = {h.strip().lower(): h for h in reader.fieldnames}

            for raw_row in reader:
                row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if v}
                date_str = row.get("date")

                steps_val = row.get("steps")
                if steps_val:
                    try:
                        metrics["steps"].append(
                            {
                                "date": date_str,
                                "value": int(float(steps_val)),
                                "unit": "count",
                                "type": METRIC_STEPS,
                            }
                        )
                    except ValueError:
                        pass

                hr_val = row.get("heart_rate")
                if hr_val:
                    try:
                        metrics["heart_rate"].append(
                            {
                                "date": date_str,
                                "value": float(hr_val),
                                "unit": "count/min",
                                "type": METRIC_HEART_RATE,
                            }
                        )
                    except ValueError:
                        pass

                sleep_val = row.get("sleep_duration")
                if sleep_val:
                    try:
                        metrics["sleep"].append(
                            {
                                "date": date_str,
                                "value": float(sleep_val),
                                "unit": "min",
                                "type": METRIC_SLEEP,
                            }
                        )
                    except ValueError:
                        pass

                cal_val = row.get("calories")
                if cal_val:
                    try:
                        metrics["calories"].append(
                            {
                                "date": date_str,
                                "value": float(cal_val),
                                "unit": "kcal",
                                "type": METRIC_CALORIES,
                            }
                        )
                    except ValueError:
                        pass

        return metrics

    # ------------------------------------------------------------------
    # Gadgetbridge HTTP server webhook
    # ------------------------------------------------------------------

    def save_gadgetbridge_webhook(self, data: Dict) -> str:
        """
        Persist incoming Gadgetbridge webhook payload to disk for audit / replay.

        Returns the absolute path of the saved file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"xiaomi_webhook_{timestamp}.json"
        filepath = os.path.realpath(os.path.join(self.export_path, filename))

        # Path-traversal guard
        if not filepath.startswith(os.path.realpath(self.export_path)):
            raise ValueError("Invalid export path resolved outside export directory")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return filepath

    def parse_gadgetbridge_webhook(self, data: Dict) -> Dict[str, List]:
        """
        Parse a single Gadgetbridge HTTP server payload.

        Expected format::

            {
                "timestamp": 1710000000,  # Unix epoch (optional)
                "heart_rate": 72,
                "steps": 8432,
                "battery": 85,
                "activity": "walking"
            }

        Returns the same normalised ``Dict[str, List]`` structure used by the
        file-based parsers so callers can treat all sources uniformly.
        """
        metrics: Dict[str, List] = {
            "heart_rate": [],
            "steps": [],
            "sleep": [],
            "calories": [],
        }

        ts = data.get("timestamp")
        if ts is not None:
            date_str = datetime.utcfromtimestamp(int(ts)).isoformat()
        else:
            date_str = datetime.utcnow().isoformat()

        hr = data.get("heart_rate")
        if hr is not None and int(hr) > 0:
            metrics["heart_rate"].append(
                {
                    "date": date_str,
                    "value": int(hr),
                    "unit": "count/min",
                    "type": METRIC_HEART_RATE,
                }
            )

        steps = data.get("steps")
        if steps is not None and int(steps) >= 0:
            metrics["steps"].append(
                {
                    "date": date_str,
                    "value": int(steps),
                    "unit": "count",
                    "type": METRIC_STEPS,
                }
            )

        return metrics

    # ------------------------------------------------------------------
    # Database sync
    # ------------------------------------------------------------------

    def sync_to_database(self, db, filepath: str) -> Dict[str, int]:
        """
        Parse ``filepath`` (auto-detecting format) and persist every metric
        record to the ``health_metrics`` table via ``db.save_health_metric()``.

        Returns a dict mapping metric category name to the count of records saved,
        e.g. ``{"heart_rate": 120, "steps": 30, "sleep": 7, "calories": 30}``.
        """
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".csv":
            metrics = self.parse_mi_fitness_export(filepath)
        else:
            metrics = self.parse_gadgetbridge_export(filepath)

        saved: Dict[str, int] = {}

        for category, records in metrics.items():
            count = 0
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
                count += 1
            if count:
                saved[category] = count

        return saved
