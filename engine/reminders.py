"""
BioMonitor - Smart Health Reminders and Recommendations Engine

Analyzes stored health data and generates personalised daily recommendations
for sleep, hydration, standing breaks, fitness, and recovery.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from storage import BioDatabase


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_hhmm(hhmm: str) -> datetime:
    """Return today's date combined with a HH:MM string."""
    today = datetime.now().date()
    h, m = hhmm.split(":")
    return datetime(today.year, today.month, today.day, int(h), int(m))


def _fmt(dt: datetime) -> str:
    """Format a datetime to HH:MM string."""
    return dt.strftime("%H:%M")


def _add_minutes(hhmm: str, minutes: int) -> str:
    return _fmt(_parse_hhmm(hhmm) + timedelta(minutes=minutes))


# ---------------------------------------------------------------------------
# RemindersEngine
# ---------------------------------------------------------------------------

class RemindersEngine:
    """Generates smart health reminders from stored BioMonitor data."""

    def __init__(self, db: BioDatabase) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # 1. Sleep recommendation
    # ------------------------------------------------------------------

    def sleep_recommendation(self, user_id: str = "default") -> Dict:
        """Analyse recent sleep data and recommend a bedtime / wake time."""
        sleep_records = self.db.get_health_metrics_history(days=14, metric_type="SleepAnalysis")
        hrv_records = self.db.get_health_metrics_history(days=7, metric_type="HeartRateVariabilitySDNN")

        # ---- compute average nightly sleep --------------------------------
        # Records may carry duration_minutes or a numeric value in hours.
        # We normalise everything to hours.
        nightly_hours: List[float] = []
        for r in sleep_records:
            val = r.get("value")
            unit = (r.get("unit") or "").lower()
            if val is None:
                continue
            try:
                val = float(val)
            except (TypeError, ValueError):
                continue
            # Heuristic: if the value looks like minutes (>24) convert to hours
            if "min" in unit or val > 24:
                val = val / 60.0
            nightly_hours.append(val)

        avg_sleep = sum(nightly_hours) / len(nightly_hours) if nightly_hours else None
        last3_avg = (
            sum(nightly_hours[-3:]) / min(3, len(nightly_hours[-3:]))
            if len(nightly_hours) >= 1
            else None
        )

        # ---- compute HRV trend -------------------------------------------
        hrv_values: List[float] = []
        for r in hrv_records:
            try:
                hrv_values.append(float(r["value"]))
            except (TypeError, ValueError, KeyError):
                pass

        hrv_trending_down = False
        if len(hrv_values) >= 3:
            # Simple: latest half average < earlier half average
            mid = len(hrv_values) // 2
            early_avg = sum(hrv_values[:mid]) / mid
            late_avg = sum(hrv_values[mid:]) / len(hrv_values[mid:])
            hrv_trending_down = late_avg < early_avg * 0.9

        # ---- derive recommendation ----------------------------------------
        target_hours = 8.0
        extra_minutes = 0
        reason_parts: List[str] = []
        priority = "low"

        if avg_sleep is not None and avg_sleep < 7:
            extra_minutes += 30
            reason_parts.append(f"average sleep ({avg_sleep:.1f}h) is below 7h")
            priority = "medium"

        if hrv_trending_down:
            extra_minutes += 30
            reason_parts.append("HRV is trending down")
            priority = "medium"

        if last3_avg is not None and last3_avg < 6:
            extra_minutes += 60
            reason_parts.append(f"last 3 nights averaged only {last3_avg:.1f}h — recovery sleep needed")
            priority = "high"

        # Default bedtime 22:30, wake 06:30 (8 h window)
        default_wake = "06:30"
        default_bed = "22:30"

        # Shift bedtime earlier by extra_minutes
        recommended_bed = _add_minutes(default_bed, -extra_minutes) if extra_minutes else default_bed
        recommended_wake = _add_minutes(default_wake, -extra_minutes) if extra_minutes else default_wake

        reason = (
            "Recommended sleep window based on: " + "; ".join(reason_parts)
            if reason_parts
            else "Sleep looks good — maintain your current schedule"
        )

        return {
            "recommended_bedtime": recommended_bed,
            "recommended_wake": recommended_wake,
            "target_hours": target_hours,
            "current_avg_hours": round(avg_sleep, 1) if avg_sleep is not None else None,
            "reason": reason,
            "priority": priority,
        }

    # ------------------------------------------------------------------
    # 2. Hydration schedule
    # ------------------------------------------------------------------

    def hydration_schedule(
        self, wake_time: str = "07:00", sleep_time: str = "23:00"
    ) -> Dict:
        """Generate an hourly water-intake schedule for the day."""
        today = datetime.now().date()
        today_str = today.isoformat()

        # Check for CrossFit sessions today
        activities_df = self.db.get_activities(
            start_date=datetime(today.year, today.month, today.day, 0, 0),
            end_date=datetime(today.year, today.month, today.day, 23, 59),
        )

        crossfit_today = 0
        crossfit_times: List[str] = []
        if not activities_df.empty:
            cf = activities_df[activities_df["is_crossfit"] == True]
            crossfit_today = len(cf)
            for _, row in cf.iterrows():
                try:
                    dt = datetime.fromisoformat(str(row["start_date"]).replace("Z", "+00:00"))
                    crossfit_times.append(_fmt(dt))
                except Exception:
                    pass

        base_glasses = 8
        total_glasses = base_glasses + crossfit_today
        glass_ml = 250
        daily_target_ml = total_glasses * glass_ml

        wake_dt = _parse_hhmm(wake_time)
        sleep_dt = _parse_hhmm(sleep_time)
        waking_minutes = int((sleep_dt - wake_dt).total_seconds() / 60)
        if waking_minutes <= 0:
            waking_minutes = 960  # 16 h default

        reminders: List[Dict] = []

        # Morning burst: 2 glasses in first hour
        reminders.append({
            "time": _fmt(wake_dt),
            "amount_ml": 250,
            "note": "Morning hydration — start the day right",
        })
        reminders.append({
            "time": _fmt(wake_dt + timedelta(minutes=30)),
            "amount_ml": 250,
            "note": "Continue morning hydration",
        })

        # Pre/post workout reminders
        for cf_time in crossfit_times:
            pre = _add_minutes(cf_time, -30)
            post = _add_minutes(cf_time, 30)
            reminders.append({"time": pre, "amount_ml": 500, "note": "Pre-workout hydration"})
            reminders.append({"time": post, "amount_ml": 500, "note": "Post-workout rehydration"})

        # Spread remaining glasses roughly every 90 minutes during waking hours
        glasses_distributed = 2 + crossfit_today * 2  # morning + workout glasses
        glasses_remaining = max(0, total_glasses - glasses_distributed)

        if glasses_remaining > 0:
            interval_min = max(60, waking_minutes // max(1, glasses_remaining))
            current = wake_dt + timedelta(minutes=90)  # skip first 90 min (morning burst)
            for _ in range(glasses_remaining):
                if current >= sleep_dt:
                    break
                note = "Stay hydrated"
                hour = current.hour
                if 12 <= hour < 13:
                    note = "Lunchtime hydration"
                elif 15 <= hour < 16:
                    note = "Afternoon hydration"
                elif 19 <= hour < 20:
                    note = "Evening hydration"
                reminders.append({"time": _fmt(current), "amount_ml": 250, "note": note})
                current += timedelta(minutes=interval_min)

        # Sort by time
        reminders.sort(key=lambda r: r["time"])

        return {
            "daily_target_ml": daily_target_ml,
            "total_glasses": total_glasses,
            "crossfit_sessions_today": crossfit_today,
            "reminders": reminders,
        }

    # ------------------------------------------------------------------
    # 3. Standing reminders
    # ------------------------------------------------------------------

    def standing_reminders(
        self, work_start: str = "09:00", work_end: str = "18:00"
    ) -> Dict:
        """Generate stand-up reminders during work hours."""
        work_start_dt = _parse_hhmm(work_start)
        work_end_dt = _parse_hhmm(work_end)
        work_minutes = int((work_end_dt - work_start_dt).total_seconds() / 60)
        if work_minutes <= 0:
            work_minutes = 540  # 9 h default

        # Check recent step count
        now = datetime.now()
        two_hours_ago = now - timedelta(hours=2)
        step_records = self.db.get_health_metrics_history(days=1, metric_type="StepCount")
        recent_steps = sum(
            float(r["value"])
            for r in step_records
            if r.get("value") is not None
            and r.get("date", "") >= two_hours_ago.isoformat()
        )
        low_steps = recent_steps < 500

        reminders: List[Dict] = []
        sit_block = 50  # minutes of sitting before standing
        stand_duration = 10  # minutes

        current = work_start_dt + timedelta(minutes=sit_block)
        while current < work_end_dt:
            note = "Stand and stretch — you've been sitting for 50 minutes"
            if low_steps:
                note += " (low step count detected — take a short walk!)"
            reminders.append({
                "time": _fmt(current),
                "duration_min": stand_duration,
                "note": note,
            })
            current += timedelta(minutes=sit_block + stand_duration)

        # Low-steps alert if no reminders cover it
        if low_steps and not reminders:
            reminders.append({
                "time": _fmt(now + timedelta(minutes=5)),
                "duration_min": 10,
                "note": "Standing alert — fewer than 500 steps in the last 2 hours",
            })

        daily_stand_target_min = (work_minutes // (sit_block + stand_duration)) * stand_duration

        return {
            "reminders": reminders,
            "daily_stand_target_min": daily_stand_target_min,
            "low_steps_alert": low_steps,
        }

    # ------------------------------------------------------------------
    # 4. Fitness reminders
    # ------------------------------------------------------------------

    def fitness_reminders(self, weekly_target: int = 3) -> Dict:
        """Smart workout scheduling based on this week's activity and HRV."""
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_start_dt = datetime(week_start.year, week_start.month, week_start.day)
        week_end_dt = week_start_dt + timedelta(days=7)

        activities_df = self.db.get_activities(
            start_date=week_start_dt, end_date=week_end_dt
        )

        sessions_this_week = 0
        last_activity_date: Optional[datetime] = None

        if not activities_df.empty:
            cf = activities_df[activities_df["is_crossfit"] == True]
            sessions_this_week = len(cf)
            if not cf.empty:
                latest_str = cf["start_date"].max()
                try:
                    last_activity_date = datetime.fromisoformat(
                        str(latest_str).replace("Z", "+00:00")
                    ).replace(tzinfo=None)
                except Exception:
                    pass

        # HRV check
        hrv_records = self.db.get_health_metrics_history(days=3, metric_type="HeartRateVariabilitySDNN")
        hrv_values = []
        for r in hrv_records:
            try:
                hrv_values.append(float(r["value"]))
            except (TypeError, ValueError, KeyError):
                pass
        latest_hrv = hrv_values[-1] if hrv_values else None
        low_hrv = latest_hrv is not None and latest_hrv < 40

        # Days since last workout
        days_since = None
        if last_activity_date:
            days_since = (today - last_activity_date).days

        # Determine recommendation
        if low_hrv:
            today_rec = "rest"
            reason = f"HRV is low ({latest_hrv:.0f} ms) — your body needs recovery"
        elif days_since is not None and days_since >= 2:
            if sessions_this_week < weekly_target:
                today_rec = "workout"
                reason = f"No workout in {days_since} days and you still need {weekly_target - sessions_this_week} session(s) this week"
            else:
                today_rec = "active_recovery"
                reason = "Weekly target met — active recovery recommended"
        elif sessions_this_week >= weekly_target:
            today_rec = "rest"
            reason = "Weekly target already met — rest up"
        else:
            today_rec = "workout"
            reason = f"{weekly_target - sessions_this_week} session(s) remaining this week"

        # Next recommended date
        if today_rec in ("rest", "active_recovery"):
            next_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            next_date = today.strftime("%Y-%m-%d")

        return {
            "sessions_this_week": sessions_this_week,
            "target": weekly_target,
            "next_recommended": next_date,
            "today_recommendation": today_rec,
            "reason": reason,
            "suggested_time": "07:00",
            "days_since_last_workout": days_since,
        }

    # ------------------------------------------------------------------
    # 5. Recovery / rest recommendation
    # ------------------------------------------------------------------

    def rest_recommendation(self) -> Dict:
        """Score recovery 0-100 from WHOOP / Oura / HRV data."""
        factors: List[str] = []
        scores: List[float] = []

        # ---- WHOOP recovery (0-100) ---------------------------------------
        whoop = self.db.get_health_metrics_history(days=2, metric_type="WhoopRecovery")
        if whoop:
            latest = whoop[-1]
            try:
                val = float(latest["value"])
                scores.append(val)
                factors.append(f"WHOOP recovery: {val:.0f}%")
            except (TypeError, ValueError):
                pass

        # ---- Oura readiness (0-100) ---------------------------------------
        oura = self.db.get_health_metrics_history(days=2, metric_type="OuraReadiness")
        if oura:
            latest = oura[-1]
            try:
                val = float(latest["value"])
                scores.append(val)
                factors.append(f"Oura readiness: {val:.0f}")
            except (TypeError, ValueError):
                pass

        # ---- HRV (normalise 20-100 ms → 0-100 score) --------------------
        hrv_records = self.db.get_health_metrics_history(
            days=2, metric_type="HeartRateVariabilitySDNN"
        )
        if hrv_records:
            try:
                hrv_val = float(hrv_records[-1]["value"])
                hrv_score = min(100.0, max(0.0, (hrv_val - 20) / (100 - 20) * 100))
                scores.append(hrv_score)
                factors.append(f"HRV: {hrv_val:.0f} ms")
            except (TypeError, ValueError, KeyError):
                pass

        if scores:
            recovery_score = round(sum(scores) / len(scores))
        else:
            # No data — neutral default
            recovery_score = 50
            factors.append("No recovery data available — assuming moderate readiness")

        if recovery_score >= 67:
            recommendation = "workout"
            color = "green"
        elif recovery_score >= 34:
            recommendation = "light"
            color = "yellow"
        else:
            recommendation = "rest"
            color = "red"

        return {
            "recovery_score": recovery_score,
            "recommendation": recommendation,
            "color": color,
            "factors": factors,
            "data_available": bool(whoop or oura or hrv_records),
        }

    # ------------------------------------------------------------------
    # 6. Daily schedule (merged timeline)
    # ------------------------------------------------------------------

    def daily_schedule(
        self,
        wake_time: str = "07:00",
        sleep_time: str = "23:00",
        work_start: str = "09:00",
        work_end: str = "18:00",
    ) -> Dict:
        """Merge all reminders into a single sorted daily timeline."""
        today = datetime.now().strftime("%Y-%m-%d")
        schedule: List[Dict] = []

        # ----- hydration --------------------------------------------------
        hydration = self.hydration_schedule(wake_time=wake_time, sleep_time=sleep_time)
        for r in hydration["reminders"]:
            schedule.append({
                "time": r["time"],
                "type": "hydration",
                "message": f"{r['note']} ({r['amount_ml']} ml)",
                "priority": "medium",
            })

        # ----- standing ---------------------------------------------------
        standing = self.standing_reminders(work_start=work_start, work_end=work_end)
        for r in standing["reminders"]:
            priority = "high" if standing.get("low_steps_alert") else "medium"
            schedule.append({
                "time": r["time"],
                "type": "standing",
                "message": r["note"],
                "priority": priority,
            })

        # ----- fitness / sleep highlights ---------------------------------
        fitness = self.fitness_reminders()
        sleep_rec = self.sleep_recommendation()
        recovery = self.rest_recommendation()

        # Morning fitness prompt
        if fitness["today_recommendation"] == "workout":
            schedule.append({
                "time": fitness["suggested_time"],
                "type": "fitness",
                "message": f"Workout time! {fitness['reason']}",
                "priority": "high",
            })
        elif fitness["today_recommendation"] == "active_recovery":
            schedule.append({
                "time": fitness["suggested_time"],
                "type": "fitness",
                "message": f"Active recovery today — {fitness['reason']}",
                "priority": "low",
            })
        else:
            schedule.append({
                "time": fitness["suggested_time"],
                "type": "fitness",
                "message": f"Rest day — {fitness['reason']}",
                "priority": "low",
            })

        # Evening bedtime reminder (30 min before recommended)
        bedtime_reminder = _add_minutes(sleep_rec["recommended_bedtime"], -30)
        schedule.append({
            "time": bedtime_reminder,
            "type": "sleep",
            "message": f"Start winding down — target bedtime {sleep_rec['recommended_bedtime']} ({sleep_rec['reason']})",
            "priority": sleep_rec["priority"],
        })

        # Recovery note at wake time
        schedule.append({
            "time": wake_time,
            "type": "recovery",
            "message": (
                f"Recovery score: {recovery['recovery_score']}/100 — "
                f"{recovery['recommendation'].replace('_', ' ').title()}"
            ),
            "priority": "high" if recovery["color"] == "red" else "medium",
        })

        # Sort by time (HH:MM string sort works correctly for 24-h times)
        schedule.sort(key=lambda x: x["time"])

        return {
            "date": today,
            "schedule": schedule,
            "recovery_color": recovery["color"],
            "recovery_score": recovery["recovery_score"],
        }
