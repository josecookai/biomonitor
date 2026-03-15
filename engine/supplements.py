from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import sys
import os

# Allow importing users package from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from users import UserProfile


# Monthly cost estimates in USD per supplement
_COST_ESTIMATES: Dict[str, float] = {
    "Magnesium Glycinate": 12.0,
    "Melatonin": 6.0,
    "L-Theanine": 10.0,
    "Omega-3 Fish Oil": 15.0,
    "Vitamin D3": 8.0,
    "Tart Cherry Extract": 18.0,
    "Creatine Monohydrate": 14.0,
    "Beta-Alanine": 12.0,
    "Whey Protein": 40.0,
    "Zinc": 7.0,
    "Probiotics": 20.0,
    "Iron": 9.0,
    "Folate": 7.0,
}


@dataclass
class Supplement:
    name: str
    dose: str
    timing: str        # "morning" / "evening" / "pre_workout" / "post_workout" / "with_meal"
    reason: str
    evidence_level: str  # "strong" / "moderate" / "emerging"
    priority: str      # "essential" / "recommended" / "optional"
    contraindications: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SupplementEngine:
    """
    Generates a personalised supplement stack based on a UserProfile and
    optional real-time health metrics (e.g. from the health_metrics DB).
    """

    def recommend(
        self,
        profile: UserProfile,
        health_metrics: Optional[Dict[str, Any]] = None,
    ) -> List[Supplement]:
        """Return a deduplicated, priority-sorted list of supplements."""
        if health_metrics is None:
            health_metrics = {}

        # Merge DB metrics into profile computed fields (non-destructive copy)
        enriched = _enrich_profile(profile, health_metrics)

        supplements: List[Supplement] = []
        supplements.extend(self._sleep_supplements(enriched))
        supplements.extend(self._recovery_supplements(enriched))
        supplements.extend(self._performance_supplements(enriched))
        supplements.extend(self._general_health(enriched))
        supplements.extend(self._female_specific(enriched))

        return self._deduplicate(supplements)

    # ------------------------------------------------------------------
    # Category builders
    # ------------------------------------------------------------------

    def _sleep_supplements(self, profile: UserProfile) -> List[Supplement]:
        poor_sleep = (
            profile.avg_sleep_hours is not None and profile.avg_sleep_hours < 7
        ) or "sleep" in profile.health_goals

        if not poor_sleep:
            return []

        return [
            Supplement(
                name="Magnesium Glycinate",
                dose="400mg",
                timing="evening",
                reason="Improves sleep quality and reduces cortisol",
                evidence_level="strong",
                priority="essential",
            ),
            Supplement(
                name="Melatonin",
                dose="0.5mg",
                timing="evening",
                reason="Regulates circadian rhythm; take 30 min before bed",
                evidence_level="strong",
                priority="recommended",
            ),
            Supplement(
                name="L-Theanine",
                dose="200mg",
                timing="evening",
                reason="Promotes relaxation without sedation",
                evidence_level="moderate",
                priority="optional",
            ),
        ]

    def _recovery_supplements(self, profile: UserProfile) -> List[Supplement]:
        low_recovery = (
            (profile.recovery_score is not None and profile.recovery_score < 60)
            or (profile.avg_hrv is not None and profile.avg_hrv < 40)
            or "recovery" in profile.health_goals
        )

        if not low_recovery:
            return []

        supps = [
            Supplement(
                name="Omega-3 Fish Oil",
                dose="2g",
                timing="with_meal",
                reason="Reduces inflammation, improves HRV",
                evidence_level="strong",
                priority="essential",
            ),
            Supplement(
                name="Vitamin D3",
                dose="2000IU",
                timing="morning",
                reason="Supports immune function and muscle recovery",
                evidence_level="strong",
                priority="essential",
            ),
            Supplement(
                name="Magnesium Glycinate",
                dose="400mg",
                timing="evening",
                reason="Reduces muscle soreness and supports recovery",
                evidence_level="strong",
                priority="essential",
            ),
            Supplement(
                name="Tart Cherry Extract",
                dose="480mg",
                timing="post_workout",
                reason="Reduces DOMS and improves sleep quality",
                evidence_level="moderate",
                priority="recommended",
            ),
        ]
        return supps

    def _performance_supplements(self, profile: UserProfile) -> List[Supplement]:
        performance_goals = {"muscle_gain", "endurance"}
        active_levels = {"active", "very_active"}

        wants_performance = bool(
            performance_goals & set(profile.health_goals)
        ) and profile.activity_level in active_levels

        if not wants_performance:
            return []

        supps = [
            Supplement(
                name="Creatine Monohydrate",
                dose="5g",
                timing="post_workout",
                reason="Increases strength and muscle mass",
                evidence_level="strong",
                priority="essential",
            ),
            Supplement(
                name="Beta-Alanine",
                dose="3.2g",
                timing="pre_workout",
                reason="Buffers lactic acid, improves endurance capacity",
                evidence_level="strong",
                priority="recommended",
            ),
        ]

        # Protein recommendation if muscle_gain is a goal
        if "muscle_gain" in profile.health_goals:
            protein_target_g = profile.weight_kg * 1.6
            supps.append(
                Supplement(
                    name="Whey Protein",
                    dose=f"25-30g (target {protein_target_g:.0f}g/day total)",
                    timing="post_workout",
                    reason=(
                        f"Supports muscle protein synthesis; aim for "
                        f"{protein_target_g:.0f}g protein/day for your weight"
                    ),
                    evidence_level="moderate",
                    priority="recommended",
                )
            )

        return supps

    def _general_health(self, profile: UserProfile) -> List[Supplement]:
        return [
            Supplement(
                name="Vitamin D3",
                dose="2000IU",
                timing="morning",
                reason="Immune support, bone health, and mood regulation",
                evidence_level="strong",
                priority="essential",
            ),
            Supplement(
                name="Zinc",
                dose="15mg",
                timing="evening",
                reason="Immune support and hormonal balance; take with meal",
                evidence_level="moderate",
                priority="recommended",
            ),
            Supplement(
                name="Probiotics",
                dose="10B CFU",
                timing="morning",
                reason="Supports gut microbiome and immune function",
                evidence_level="moderate",
                priority="optional",
            ),
        ]

    def _female_specific(self, profile: UserProfile) -> List[Supplement]:
        if profile.sex != "female":
            return []

        return [
            Supplement(
                name="Iron",
                dose="18mg",
                timing="with_meal",
                reason="Prevents deficiency, supports energy levels and oxygen transport",
                evidence_level="strong",
                priority="essential",
            ),
            Supplement(
                name="Folate",
                dose="400mcg",
                timing="morning",
                reason="Cellular health and DNA synthesis support",
                evidence_level="strong",
                priority="essential",
            ),
        ]

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _deduplicate(self, supplements: List[Supplement]) -> List[Supplement]:
        """
        Keep the first occurrence of each supplement name.
        Earlier items have higher priority (essential > recommended > optional),
        so the first occurrence always wins.
        """
        seen: set = set()
        unique: List[Supplement] = []
        for s in supplements:
            if s.name not in seen:
                seen.add(s.name)
                unique.append(s)
        return unique

    def as_daily_plan(self, supplements: List[Supplement]) -> Dict[str, Any]:
        """
        Group supplements by timing into a structured daily plan.

        Returns:
            {
                "morning": [...],
                "pre_workout": [...],
                "post_workout": [...],
                "evening": [...],
                "with_meal": [...],
                "total_supplements": int,
                "estimated_monthly_cost_usd": float,
            }
        """
        plan: Dict[str, List[Dict]] = {
            "morning": [],
            "pre_workout": [],
            "post_workout": [],
            "evening": [],
            "with_meal": [],
        }

        for supp in supplements:
            timing_key = supp.timing
            if timing_key not in plan:
                # Fallback: unknown timings go to morning
                timing_key = "morning"
            plan[timing_key].append(supp.to_dict())

        total_cost = sum(
            _COST_ESTIMATES.get(s.name, 10.0) for s in supplements
        )

        return {
            **plan,
            "total_supplements": len(supplements),
            "estimated_monthly_cost_usd": round(total_cost, 2),
        }


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _enrich_profile(profile: UserProfile, metrics: Dict[str, Any]) -> UserProfile:
    """
    Return a new UserProfile with computed fields filled from health_metrics
    if they are not already set on the profile.
    All original profile fields are preserved immutably.
    """
    from dataclasses import replace

    updates: Dict[str, Any] = {}

    if profile.avg_sleep_hours is None and "avg_sleep_hours" in metrics:
        updates["avg_sleep_hours"] = metrics["avg_sleep_hours"]

    if profile.avg_hrv is None and "avg_hrv" in metrics:
        updates["avg_hrv"] = metrics["avg_hrv"]

    if profile.avg_resting_hr is None and "avg_resting_hr" in metrics:
        updates["avg_resting_hr"] = metrics["avg_resting_hr"]

    if profile.recovery_score is None and "recovery_score" in metrics:
        updates["recovery_score"] = metrics["recovery_score"]

    if not updates:
        return profile

    return replace(profile, **updates)
