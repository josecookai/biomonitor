"""
BioMonitor - Oura Ring Collector
Collect sleep, readiness, activity, and biometric data from Oura Ring API v2
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests

from . import load_config, _REQUEST_TIMEOUT


class OuraCollector:
    """Collect health data from Oura Ring API v2"""

    base_url = "https://api.ouraring.com/v2"

    def __init__(self, access_token: str = None):
        config = load_config()
        oura_config = config.get('oura', {})
        self.access_token = access_token or oura_config.get('access_token')

    def _headers(self) -> Dict[str, str]:
        """Build Authorization headers"""
        return {"Authorization": f"Bearer {self.access_token}"}

    def _get(self, path: str, params: Dict) -> Dict:
        """Perform a GET request against the Oura v2 API."""
        response = requests.get(
            f"{self.base_url}{path}",
            headers=self._headers(),
            params=params,
            timeout=_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def get_daily_readiness(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Fetch daily readiness scores.

        Args:
            start_date: ISO date string, e.g. "2026-03-08"
            end_date:   ISO date string, e.g. "2026-03-15"

        Returns:
            List of readiness record dicts from the Oura API.
        """
        data = self._get(
            "/usercollection/daily_readiness",
            {"start_date": start_date, "end_date": end_date},
        )
        return data.get("data", [])

    def get_daily_sleep(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Fetch daily sleep scores and duration.

        Args:
            start_date: ISO date string
            end_date:   ISO date string

        Returns:
            List of sleep record dicts from the Oura API.
        """
        data = self._get(
            "/usercollection/daily_sleep",
            {"start_date": start_date, "end_date": end_date},
        )
        return data.get("data", [])

    def get_daily_activity(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Fetch daily activity scores.

        Args:
            start_date: ISO date string
            end_date:   ISO date string

        Returns:
            List of activity record dicts from the Oura API.
        """
        data = self._get(
            "/usercollection/daily_activity",
            {"start_date": start_date, "end_date": end_date},
        )
        return data.get("data", [])

    def get_heart_rate(self, start_datetime: str, end_datetime: str) -> List[Dict]:
        """
        Fetch heart rate samples.

        Args:
            start_datetime: ISO datetime string, e.g. "2026-03-08T00:00:00"
            end_datetime:   ISO datetime string

        Returns:
            List of heart rate sample dicts from the Oura API.
        """
        data = self._get(
            "/usercollection/heartrate",
            {"start_datetime": start_datetime, "end_datetime": end_datetime},
        )
        return data.get("data", [])

    def get_hrv(self, start_datetime: str, end_datetime: str) -> List[Dict]:
        """
        Fetch HRV (Heart Rate Variability) samples.

        The Oura v2 API exposes HRV inside the sleep document under
        `hrv.items` (5-minute averages).  This method fetches the sleep
        records for the requested window and normalises each HRV sample
        into the same flat shape returned by get_heart_rate().

        Args:
            start_datetime: ISO datetime string
            end_datetime:   ISO datetime string

        Returns:
            List of HRV sample dicts: {"timestamp": str, "hrv": float}
        """
        # The /v2/usercollection/heartrate endpoint does not expose HRV.
        # HRV is available inside the sleep object under hrv.items /
        # hrv.interval.  We pull the sleep detail endpoint instead.
        start_date = start_datetime[:10]
        end_date = end_datetime[:10]

        data = self._get(
            "/usercollection/sleep",
            {"start_date": start_date, "end_date": end_date},
        )
        records = data.get("data", [])

        samples: List[Dict] = []
        for record in records:
            hrv_block = record.get("hrv") or {}
            items = hrv_block.get("items") or []
            interval = hrv_block.get("interval", 300)  # seconds, default 5 min
            bedtime_start = record.get("bedtime_start", "")

            try:
                base_ts = datetime.fromisoformat(bedtime_start.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                base_ts = None

            for idx, hrv_value in enumerate(items):
                if hrv_value is None:
                    continue
                if base_ts is not None:
                    sample_ts = (base_ts + timedelta(seconds=idx * interval)).isoformat()
                else:
                    sample_ts = bedtime_start
                samples.append({"timestamp": sample_ts, "hrv": hrv_value})

        return samples

    def sync_to_database(self, db, days: int = 7) -> Dict[str, int]:
        """
        Sync the last *days* of Oura data into the health_metrics table.

        Saves:
            - Readiness score          → metric_type="OuraReadiness"
            - Sleep score              → metric_type="OuraSleepScore"
            - Sleep total duration (s) → metric_type="OuraSleepDuration"
            - Activity score           → metric_type="OuraActivityScore"
            - Heart rate samples       → metric_type="HeartRate"
            - HRV samples              → metric_type="HeartRateVariability"

        Args:
            db:   BioDatabase instance
            days: How many days back to sync (1–90)

        Returns:
            Dict with counts of records saved per metric type, plus a
            "skipped" key with an error message when the token is missing.
        """
        if not self.access_token:
            message = (
                "Oura access token is not configured. "
                "Add 'oura.access_token' to config.yaml and restart the server."
            )
            print(f"[OuraCollector] {message}")
            return {"skipped": message}

        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days)
        start_date = start_dt.strftime("%Y-%m-%d")
        end_date = end_dt.strftime("%Y-%m-%d")
        start_datetime = start_dt.isoformat()
        end_datetime = end_dt.isoformat()

        counts: Dict[str, int] = {
            "OuraReadiness": 0,
            "OuraSleepScore": 0,
            "OuraSleepDuration": 0,
            "OuraActivityScore": 0,
            "HeartRate": 0,
            "HeartRateVariability": 0,
        }

        # --- Readiness ---
        try:
            for record in self.get_daily_readiness(start_date, end_date):
                score = record.get("score")
                if score is None:
                    continue
                saved = db.save_health_metric({
                    "date": record.get("day"),
                    "metric_type": "OuraReadiness",
                    "value": float(score),
                    "unit": "score",
                    "source": "oura",
                })
                if saved:
                    counts["OuraReadiness"] += 1
        except Exception as exc:
            print(f"[OuraCollector] Error fetching readiness: {exc}")

        # --- Sleep ---
        try:
            for record in self.get_daily_sleep(start_date, end_date):
                sleep_score = record.get("score")
                if sleep_score is not None:
                    saved = db.save_health_metric({
                        "date": record.get("day"),
                        "metric_type": "OuraSleepScore",
                        "value": float(sleep_score),
                        "unit": "score",
                        "source": "oura",
                    })
                    if saved:
                        counts["OuraSleepScore"] += 1

                duration = record.get("contributors", {}).get("total_sleep") or record.get("total_sleep_duration")
                if duration is not None:
                    saved = db.save_health_metric({
                        "date": record.get("day"),
                        "metric_type": "OuraSleepDuration",
                        "value": float(duration),
                        "unit": "seconds",
                        "source": "oura",
                    })
                    if saved:
                        counts["OuraSleepDuration"] += 1
        except Exception as exc:
            print(f"[OuraCollector] Error fetching sleep: {exc}")

        # --- Activity ---
        try:
            for record in self.get_daily_activity(start_date, end_date):
                score = record.get("score")
                if score is None:
                    continue
                saved = db.save_health_metric({
                    "date": record.get("day"),
                    "metric_type": "OuraActivityScore",
                    "value": float(score),
                    "unit": "score",
                    "source": "oura",
                })
                if saved:
                    counts["OuraActivityScore"] += 1
        except Exception as exc:
            print(f"[OuraCollector] Error fetching activity: {exc}")

        # --- Heart Rate ---
        try:
            for record in self.get_heart_rate(start_datetime, end_datetime):
                bpm = record.get("bpm")
                if bpm is None:
                    continue
                saved = db.save_health_metric({
                    "date": record.get("timestamp"),
                    "metric_type": "HeartRate",
                    "value": float(bpm),
                    "unit": "bpm",
                    "source": "oura",
                })
                if saved:
                    counts["HeartRate"] += 1
        except Exception as exc:
            print(f"[OuraCollector] Error fetching heart rate: {exc}")

        # --- HRV ---
        try:
            for sample in self.get_hrv(start_datetime, end_datetime):
                hrv_val = sample.get("hrv")
                if hrv_val is None:
                    continue
                saved = db.save_health_metric({
                    "date": sample.get("timestamp"),
                    "metric_type": "HeartRateVariability",
                    "value": float(hrv_val),
                    "unit": "ms",
                    "source": "oura",
                })
                if saved:
                    counts["HeartRateVariability"] += 1
        except Exception as exc:
            print(f"[OuraCollector] Error fetching HRV: {exc}")

        return counts
