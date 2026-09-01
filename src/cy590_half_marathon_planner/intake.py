"""Structured intake form definitions, validation, and message construction."""

import re

DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]

SURFACES = ["Road", "Trail"]

EXPERIENCE = ["Beginner", "Intermediate", "Advanced"]

CROSS_TRAINING = [
    "None",
    "Cycling",
    "Swimming",
    "Strength training",
    "Rowing",
    "Elliptical",
    "Yoga",
    "Pilates",
    "Hiking",
    "Walking",
]

RACE_DISTANCES = [
    "No recent race",
    "1 mile",
    "2 mile",
    "5K",
    "10K",
    "10 mile",
    "Half marathon",
    "Marathon",
]

TEMPERATURES = [
    "Extremely hot (100F and above)",
    "Very hot (85-99F)",
    "Hot (70-84F)",
    "Mild (55-69F)",
    "Cold (40-54F)",
    "Very cold (25-39F)",
    "Extremely cold (24F and below)",
]

DEVICES = ["None", "GPS watch", "Heart-rate monitor", "Both"]

CROSS_TRAINING_SLOTS = 5
MAX_FREE_TEXT = 500
MIN_RUN_MILES = 3.0
MIN_RUNNING_DAYS = 3


def sanitize(text: str) -> str:
    """Reduce a free-text field to plain, bounded, tag-free content."""
    if not text:
        return "None provided"
    text = str(text)[:MAX_FREE_TEXT]
    text = re.sub(r"[<>]", "", text)                    # no tags
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text)        # no control chars
    text = re.sub(r"\s+", " ", text).strip()            # single spaces
    return text or "None provided"


def _hms(hours: int, minutes: int, seconds: int) -> str:
    return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"


def _total_seconds(hours: int, minutes: int, seconds: int) -> int:
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)

def recommended_running_days(mileage: int, days_free: int) -> int:
    """How many running days the starting weekly mileage actually supports."""
    remaining = float(mileage) * 0.70          # after a 30% long run
    supportable = int(remaining // MIN_RUN_MILES) + 1
    supportable = max(MIN_RUNNING_DAYS, supportable)
    return min(int(days_free), supportable)


def _cross_training_rows(cross_values: tuple) -> list[tuple[str, int]]:
    """cross_values arrives as (type, days) repeated per slot."""
    rows = []
    for i in range(0, len(cross_values), 2):
        ct_type, ct_days = cross_values[i:i + 2]
        if ct_type and ct_type != "None" and int(ct_days) > 0:
            rows.append((ct_type, int(ct_days)))
    return rows


def validate(
    weeks, goal_h, goal_m, goal_s, mileage, long_run_day,
    days_unavailable, longest_run, race_distance, race_h, race_m, race_s,
    cross_values,
) -> list[str]:
    """Return a list of human-readable problems. Empty list means valid."""
    errors = []
    days_unavailable = days_unavailable or []
    days_free = 7 - len(days_unavailable)

    if _total_seconds(goal_h, goal_m, goal_s) == 0:
        errors.append("Goal half-marathon time cannot be 0:00:00.")

    if days_free < MIN_RUNNING_DAYS:
        errors.append(
            f"You marked {len(days_unavailable)} day(s) unavailable, leaving "
            f"{days_free}. A half-marathon plan needs at least "
            f"{MIN_RUNNING_DAYS} training days per week."
        )

    if long_run_day in days_unavailable:
        errors.append(
            f"{long_run_day} is your preferred long-run day but is also "
            "marked unavailable."
        )

    if float(longest_run) > float(mileage):
        errors.append(
            "Your longest recent run is greater than your weekly mileage. "
            "Please check both values."
        )

    if race_distance != "No recent race":
        if _total_seconds(race_h, race_m, race_s) == 0:
            errors.append(
                f"You selected a recent {race_distance} but left the time "
                "at 0:00:00."
            )

    rows = _cross_training_rows(cross_values)
    if sum(days for _, days in rows) > days_free:
        errors.append(
            f"Cross-training totals more days than you have available "
            f"({days_free})."
        )

    return errors


def build_intake_message(
    surface, cross_values, weeks, goal_h, goal_m, goal_s, mileage,
    experience, injuries, goals, long_run_day, race_surface, elevation,
    days_unavailable, longest_run, race_distance, race_h, race_m, race_s,
    age, temperature, device,
) -> str:
    """Turn validated form values into a single numbered intake message."""
    rows = _cross_training_rows(cross_values)
    if rows:
        cross_text = "; ".join(
            f"{t}: {d} day(s) per week" for t, d in rows
        )
    else:
        cross_text = "None"

    days_unavailable = days_unavailable or []
    unavailable = ", ".join(days_unavailable) if days_unavailable else "None"
    days_free = 7 - len(days_unavailable)
    rec_days = recommended_running_days(mileage, days_free)

    if race_distance == "No recent race":
        race_text = "No recent race or time trial"
    else:
        race_text = f"{race_distance} in {_hms(race_h, race_m, race_s)}"

    lines = [
        "All intake questions are answered below. Do not ask for more "
        "information; generate the full plan now.",
        "",
        f"1. Preferred training surface: {surface}",
        f"2. Cross-training: {cross_text}",
        f"3. Weeks until the half marathon: {int(weeks)}",
        f"4. Goal half-marathon time: {_hms(goal_h, goal_m, goal_s)}",
        f"5. Current weekly mileage: {int(mileage)} miles",
        f"6. Level of experience: {experience}",
        f"7. Injuries or health concerns (current or historical): "
        f"{sanitize(injuries)}",
        f"8. Specific goals or preferences: {sanitize(goals)}",
        f"9. Preferred long-run day: {long_run_day}",
        f"10. Race-day surface: {race_surface}",
        f"11. Race elevation gain: {int(elevation)} feet",
        f"12. Days unavailable for any training: {unavailable}",
        f"13. Longest run in the past month: {int(longest_run)} miles",
        f"14. Recent race result: {race_text}",
        f"15. Age: {int(age)}",
        f"16. Training temperature: {temperature}",
        f"17. Training device: {device}",
        "",
        f"Derived constraint: {days_free} day(s) per week are available. "
        f"At {int(mileage)} miles per week the plan should start with about "
        f"{rec_days} running day(s) per week, growing toward {days_free} only "
        f"as weekly mileage grows enough to keep every run at least 3 miles.",
    ]
    return "\n".join(lines)