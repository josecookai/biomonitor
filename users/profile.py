from dataclasses import dataclass, field, asdict
from typing import Optional, List
import yaml
import os


@dataclass
class UserProfile:
    user_id: str
    name: str
    age: int
    weight_kg: float
    height_cm: float
    sex: str  # "male" / "female" / "other"
    activity_level: str  # "sedentary" / "light" / "moderate" / "active" / "very_active"
    device: str  # "oura" / "whoop" / "xiaomi" / "apple_watch" / "strava_only"
    health_goals: List[str] = field(default_factory=list)
    # ["sleep", "recovery", "weight_loss", "muscle_gain", "endurance", "general_health"]
    conditions: List[str] = field(default_factory=list)
    # ["hypertension", "diabetes", "vegetarian", ...]
    # Computed fields (filled from health_metrics DB)
    avg_sleep_hours: Optional[float] = None
    avg_hrv: Optional[float] = None
    avg_resting_hr: Optional[float] = None
    recovery_score: Optional[float] = None


def profile_path(user_id: str) -> str:
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'users', 'data')
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"{user_id}.yaml")


def load_profile(user_id: str) -> Optional[UserProfile]:
    path = profile_path(user_id)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = yaml.safe_load(f)
    return UserProfile(**data)


def save_profile(profile: UserProfile) -> None:
    path = profile_path(profile.user_id)
    with open(path, 'w') as f:
        yaml.safe_dump(asdict(profile), f, allow_unicode=True)
