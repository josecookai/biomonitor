"""
BioMonitor - WHOOP Collector
Collect recovery, sleep, strain, and workout data from WHOOP API v1 (OAuth 2.0)
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests

from . import load_config, save_config, _REQUEST_TIMEOUT


class WhoopCollector:
    """Collect health data from WHOOP API v1"""

    base_url = "https://api.prod.whoop.com/developer"
    token_url = "https://api.prod.whoop.com/oauth/oauth2/token"
    auth_url = "https://api.prod.whoop.com/oauth/oauth2/auth"

    def __init__(
        self,
        access_token: str = None,
        refresh_token: str = None,
        client_id: str = None,
        client_secret: str = None,
    ):
        config = load_config()
        whoop_config = config.get("whoop", {})

        self.access_token = access_token or whoop_config.get("access_token")
        self.refresh_token = refresh_token or whoop_config.get("refresh_token")
        self.client_id = client_id or whoop_config.get("client_id")
        self.client_secret = client_secret or whoop_config.get("client_secret")
        self.redirect_uri = whoop_config.get(
            "redirect_uri", "http://localhost:8000/api/whoop/callback"
        )

    def get_authorization_url(self) -> str:
        """Build the OAuth 2.0 authorization URL for the user to visit."""
        scopes = "read:recovery read:sleep read:workout read:cycles read:body_measurement"
        params = (
            f"client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={scopes.replace(' ', '%20')}"
            f"&response_type=code"
        )
        return f"{self.auth_url}?{params}"

    def exchange_code_for_tokens(self, code: str) -> bool:
        """
        Exchange an OAuth authorization code for access + refresh tokens.
        Persists tokens to config.yaml on success.

        Args:
            code: The authorization code received from the WHOOP callback.

        Returns:
            True if tokens were obtained and saved; False otherwise.
        """
        if not self.client_id or not self.client_secret:
            return False

        response = requests.post(
            self.token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=_REQUEST_TIMEOUT,
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data.get("refresh_token", self.refresh_token)
            self._persist_tokens()
            return True

        print(
            f"[WhoopCollector] Token exchange failed: "
            f"{response.status_code} {response.text}"
        )
        return False

    def refresh_access_token(self) -> bool:
        """
        Refresh the access token using the stored refresh token.
        Persists the new tokens to config.yaml on success.

        Returns:
            True if the refresh succeeded; False otherwise.
        """
        if not self.refresh_token:
            return False

        response = requests.post(
            self.token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=_REQUEST_TIMEOUT,
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data.get("refresh_token", self.refresh_token)
            self._persist_tokens()
            return True

        print(
            f"[WhoopCollector] Token refresh failed: "
            f"{response.status_code} {response.text}"
        )
        return False

    def _persist_tokens(self) -> None:
        """Write updated tokens back to config.yaml."""
        try:
            config = load_config()
            config.setdefault("whoop", {})
            config["whoop"]["access_token"] = self.access_token
            config["whoop"]["refresh_token"] = self.refresh_token
            save_config(config)
        except Exception as exc:
            print(f"[WhoopCollector] Warning: could not persist tokens: {exc}")

    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make an authenticated GET request to the WHOOP API.
        Automatically refreshes the access token on 401 and retries once.

        Args:
            endpoint: API path, e.g. "/v1/recovery"
            params:   Query parameters dict.

        Returns:
            Parsed JSON response dict.

        Raises:
            requests.HTTPError: On non-2xx responses that cannot be recovered.
        """
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{self.base_url}{endpoint}"

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=_REQUEST_TIMEOUT,
        )

        if response.status_code == 401:
            if self.refresh_access_token():
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=_REQUEST_TIMEOUT,
                )

        response.raise_for_status()
        return response.json()

    def _get_paginated(self, endpoint: str, start: str, end: str) -> List[Dict]:
        """
        Fetch all pages from a WHOOP cursor-based paginated endpoint.

        WHOOP returns a JSON body with:
          - "records": list of data items for that page
          - "next_token": cursor for the next page (absent when done)

        Args:
            endpoint: API path, e.g. "/v1/recovery"
            start:    ISO 8601 datetime string for the range start
            end:      ISO 8601 datetime string for the range end

        Returns:
            Flat list of all record dicts across all pages.
        """
        records: List[Dict] = []
        params: Dict = {"start": start, "end": end, "limit": 25}

        while True:
            resp = self._get(endpoint, params)
            records.extend(resp.get("records", []))
            next_token = resp.get("next_token")
            if not next_token:
                break
            params = {"start": start, "end": end, "limit": 25, "nextToken": next_token}

        return records

    def get_recovery(self, start: str, end: str) -> List[Dict]:
        """
        Fetch recovery records from the WHOOP API.

        Each record contains recovery_score, hrv_rmssd_milli,
        resting_heart_rate, and sleep_performance_percentage.

        Args:
            start: ISO 8601 datetime string, e.g. "2026-03-08T00:00:00.000Z"
            end:   ISO 8601 datetime string

        Returns:
            List of recovery record dicts.
        """
        return self._get_paginated("/v1/recovery", start, end)

    def get_sleep(self, start: str, end: str) -> List[Dict]:
        """
        Fetch sleep records from the WHOOP API.

        Each record score contains total_in_bed_time_milli,
        total_sleep_time_milli, and sleep_performance_percentage.

        Args:
            start: ISO 8601 datetime string
            end:   ISO 8601 datetime string

        Returns:
            List of sleep record dicts.
        """
        return self._get_paginated("/v1/sleep", start, end)

    def get_cycles(self, start: str, end: str) -> List[Dict]:
        """
        Fetch daily physiological cycle (strain) records from the WHOOP API.

        Each record score contains strain, kilojoule, average_heart_rate,
        and max_heart_rate.

        Args:
            start: ISO 8601 datetime string
            end:   ISO 8601 datetime string

        Returns:
            List of cycle record dicts.
        """
        return self._get_paginated("/v1/cycle", start, end)

    def get_workouts(self, start: str, end: str) -> List[Dict]:
        """
        Fetch individual workout records from the WHOOP API.

        Args:
            start: ISO 8601 datetime string
            end:   ISO 8601 datetime string

        Returns:
            List of workout record dicts.
        """
        return self._get_paginated("/v1/workout", start, end)

    def sync_to_database(self, db, days: int = 7) -> Dict[str, int]:
        """
        Sync the last *days* of WHOOP data into the health_metrics table.

        Saves the following metrics:
            - recovery_score           → metric_type="WhoopRecovery"
            - hrv_rmssd_milli          → metric_type="HeartRateVariability"
            - resting_heart_rate       → metric_type="HeartRate"
            - sleep_performance_pct    → metric_type="WhoopSleepScore"
            - total_sleep_time_milli   → metric_type="SleepAnalysis" (hours)
            - cycle strain             → metric_type="WhoopStrain"

        Args:
            db:   BioDatabase instance
            days: How many days back to sync (1–90)

        Returns:
            Dict mapping metric_type to the number of records saved, plus a
            "skipped" key with an explanation message when tokens are missing.
        """
        if not self.access_token:
            message = (
                "WHOOP access token is not configured. "
                "Complete the OAuth flow via GET /api/whoop/auth-url, "
                "then POST /api/whoop/callback with the code."
            )
            print(f"[WhoopCollector] {message}")
            return {"skipped": message}

        end_dt = datetime.utcnow()
        start_dt = end_dt - timedelta(days=days)
        start = start_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end = end_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        counts: Dict[str, int] = {
            "WhoopRecovery": 0,
            "HeartRateVariability": 0,
            "HeartRate": 0,
            "WhoopSleepScore": 0,
            "SleepAnalysis": 0,
            "WhoopStrain": 0,
        }

        # --- Recovery (score, HRV, resting HR, sleep performance) ---
        try:
            for record in self.get_recovery(start, end):
                cycle_start = record.get("created_at") or record.get("updated_at", "")
                score_block = record.get("score") or {}

                recovery_score = score_block.get("recovery_score")
                if recovery_score is not None:
                    saved = db.save_health_metric({
                        "date": cycle_start,
                        "metric_type": "WhoopRecovery",
                        "value": float(recovery_score),
                        "unit": "score",
                        "source": "whoop",
                    })
                    if saved:
                        counts["WhoopRecovery"] += 1

                hrv = score_block.get("hrv_rmssd_milli")
                if hrv is not None:
                    saved = db.save_health_metric({
                        "date": cycle_start,
                        "metric_type": "HeartRateVariability",
                        "value": float(hrv),
                        "unit": "ms",
                        "source": "whoop",
                    })
                    if saved:
                        counts["HeartRateVariability"] += 1

                rhr = score_block.get("resting_heart_rate")
                if rhr is not None:
                    saved = db.save_health_metric({
                        "date": cycle_start,
                        "metric_type": "HeartRate",
                        "value": float(rhr),
                        "unit": "bpm",
                        "source": "whoop",
                    })
                    if saved:
                        counts["HeartRate"] += 1

                sleep_perf = score_block.get("sleep_performance_percentage")
                if sleep_perf is not None:
                    saved = db.save_health_metric({
                        "date": cycle_start,
                        "metric_type": "WhoopSleepScore",
                        "value": float(sleep_perf),
                        "unit": "%",
                        "source": "whoop",
                    })
                    if saved:
                        counts["WhoopSleepScore"] += 1

        except Exception as exc:
            print(f"[WhoopCollector] Error fetching recovery: {exc}")

        # --- Sleep (total sleep duration in hours) ---
        try:
            for record in self.get_sleep(start, end):
                sleep_start = record.get("start") or record.get("created_at", "")
                score_block = record.get("score") or {}

                total_ms = score_block.get("total_sleep_time_milli")
                if total_ms is not None:
                    hours = float(total_ms) / 3_600_000
                    saved = db.save_health_metric({
                        "date": sleep_start,
                        "metric_type": "SleepAnalysis",
                        "value": round(hours, 4),
                        "unit": "hours",
                        "source": "whoop",
                    })
                    if saved:
                        counts["SleepAnalysis"] += 1

        except Exception as exc:
            print(f"[WhoopCollector] Error fetching sleep: {exc}")

        # --- Cycles (daily strain) ---
        try:
            for record in self.get_cycles(start, end):
                cycle_start = record.get("start") or record.get("created_at", "")
                score_block = record.get("score") or {}

                strain = score_block.get("strain")
                if strain is not None:
                    saved = db.save_health_metric({
                        "date": cycle_start,
                        "metric_type": "WhoopStrain",
                        "value": float(strain),
                        "unit": "strain",
                        "source": "whoop",
                    })
                    if saved:
                        counts["WhoopStrain"] += 1

        except Exception as exc:
            print(f"[WhoopCollector] Error fetching cycles: {exc}")

        return counts
