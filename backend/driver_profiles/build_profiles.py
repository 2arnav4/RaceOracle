"""
Build simple driver style profiles using FastF1 telemetry.

This script:
- Downloads F1 race data via FastF1
- Computes lap-level features for each driver (speed, throttle, braking, etc.)
- Aggregates them into a rough 'style profile' per driver
- Saves everything into driver_profiles/driver_profiles.json

It does NOT touch your FastAPI backend or frontend.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

import fastf1
import numpy as np
import pandas as pd


# ---------- CONFIG YOU CAN TWEAK LATER ---------- #

# Where FastF1 will cache downloaded timing/telemetry
BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "fastf1_cache"

# Some drivers to analyse (use official 3-letter codes)
DRIVERS = [
    {"code": "VER", "name": "Max Verstappen"},
    {"code": "HAM", "name": "Lewis Hamilton"},
    {"code": "LEC", "name": "Charles Leclerc"},
]

# A few recent races to average over
# FastF1 expects the *event name* exactly as in the F1 calendar.
SESSIONS = [
    {"year": 2023, "event": "Bahrain Grand Prix", "session": "R"},
    {"year": 2023, "event": "British Grand Prix", "session": "R"},
    {"year": 2023, "event": "Italian Grand Prix", "session": "R"},
]


# ---------- DATA MODELS ---------- #

@dataclass
class LapFeatures:
    lap_number: int
    lap_time_s: float
    mean_speed: float
    max_speed: float
    speed_std: float
    full_throttle_pct: float
    heavy_brake_pct: float
    coasting_pct: float
    tyre_compound: str | None
    stint: int | None


@dataclass
class SessionAggregate:
    session_key: str
    driver_code: str

    laps_used: int
    avg_lap_time_s: float
    mean_speed: float
    max_speed: float
    full_throttle_pct: float
    heavy_brake_pct: float
    coasting_pct: float

    aggression_score: float
    braking_risk: float
    style_tag: str


@dataclass
class DriverProfile:
    driver_code: str
    driver_name: str
    sessions: List[SessionAggregate]
    overall: Dict[str, float]


# ---------- FASTF1 SETUP ---------- #

def ensure_cache():
    """Enable FastF1 cache in a local folder."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(CACHE_DIR))


# ---------- FEATURE ENGINEERING ---------- #

def _normalise_percent(series: pd.Series) -> pd.Series:
    """
    FastF1 sometimes gives Throttle/Brake as 0–100, sometimes 0–1.
    Normalise everything to 0–1.
    """
    if series.empty:
        return series
    max_val = float(series.max())
    if max_val == 0:
        return series
    if max_val > 1.5:  # assume it's 0–100
        return series / 100.0
    return series


def extract_lap_features(lap) -> Optional[LapFeatures]:
    """
    Given a single FastF1 Lap object, compute lap-level features.
    Returns None if telemetry is missing or LapTime is invalid.
    """
    if pd.isna(lap.LapTime):
        return None

    try:
        tel = lap.get_telemetry().add_distance()
    except Exception:
        # Some old laps / sessions can fail to load telemetry
        return None

    if tel.empty:
        return None

    speeds = tel["Speed"]
    throttle = _normalise_percent(tel["Throttle"])
    brake = _normalise_percent(tel["Brake"])

    mean_speed = float(speeds.mean())
    max_speed = float(speeds.max())
    speed_std = float(speeds.std())

    # Fraction of samples > 90% throttle
    full_throttle_pct = float((throttle > 0.9).mean())

    # Fraction of samples with heavy braking (> 70% input)
    heavy_brake_pct = float((brake > 0.7).mean())

    # Fraction of samples where neither throttle nor brake is used much
    coasting_pct = float(
        ((throttle < 0.1) & (brake < 0.1)).mean()
    )

    lap_time_s = float(lap.LapTime.total_seconds())

    return LapFeatures(
        lap_number=int(lap.LapNumber),
        lap_time_s=lap_time_s,
        mean_speed=mean_speed,
        max_speed=max_speed,
        speed_std=speed_std,
        full_throttle_pct=full_throttle_pct,
        heavy_brake_pct=heavy_brake_pct,
        coasting_pct=coasting_pct,
        tyre_compound=str(getattr(lap, "Compound", "")) if hasattr(lap, "Compound") else None,
        stint=int(getattr(lap, "Stint", 0)) if hasattr(lap, "Stint") else None,
    )


def aggregate_session(
    session,
    driver_code: str,
    fast_laps_only: bool = True,
    max_laps: int = 10,
) -> Optional[SessionAggregate]:
    """
    Build one SessionAggregate for a given driver in a given session.
    """
    laps = session.laps.pick_driver(driver_code)

    if laps.empty:
        return None

    if fast_laps_only:
        # drop in/out laps, slow safety-car laps etc.
        laps = laps.pick_quicklaps()

    if laps.empty:
        return None

    # Take up to N fastest laps
    laps = laps.nsmallest(max_laps, "LapTime")

    feature_objects: List[LapFeatures] = []
    for _, lap in laps.iterrows():
        lf = extract_lap_features(lap)
        if lf is not None:
            feature_objects.append(lf)

    if not feature_objects:
        return None

    df = pd.DataFrame([asdict(f) for f in feature_objects])

    # Basic aggregates
    laps_used = int(len(df))
    avg_lap_time_s = float(df["lap_time_s"].mean())
    mean_speed = float(df["mean_speed"].mean())
    max_speed = float(df["max_speed"].max())
    full_throttle_pct = float(df["full_throttle_pct"].mean())
    heavy_brake_pct = float(df["heavy_brake_pct"].mean())
    coasting_pct = float(df["coasting_pct"].mean())

    # ---- Rough style metrics (heuristic, but grounded) ----
    # Normalise mean speed relative to a typical F1 top speed (~330 km/h)
    speed_norm = min(mean_speed / 330.0, 1.0)

    # Aggression = pushes throttle, keeps speed high, avoids coasting
    aggression_score = float(
        0.5 * full_throttle_pct
        + 0.3 * (1.0 - coasting_pct)
        + 0.2 * speed_norm
    )

    # Braking risk = how often they’re in heavy braking zones
    braking_risk = heavy_brake_pct

    # Label the style roughly
    if aggression_score > 0.72 and braking_risk > 0.16:
        style_tag = "very_aggressive"
    elif aggression_score > 0.62:
        style_tag = "aggressive"
    elif aggression_score < 0.45 and braking_risk < 0.08:
        style_tag = "very_cautious"
    elif aggression_score < 0.52:
        style_tag = "cautious"
    else:
        style_tag = "balanced"

    # ---- Build a session key that's robust to FastF1 version changes ----
    try:
        # Newer FastF1: event + date are attributes, session has .name
        session_key = f"{session.event.Name} {session.event.Date.year} {session.name}"
    except Exception:
        # Fallback for older structures
        event_name = getattr(session.event, "Name", "Unknown")
        event_date = getattr(session.event, "Date", None)
        year = event_date.year if event_date else "Unknown"
        name = getattr(session, "name", "Unknown")
        session_key = f"{event_name} {year} {name}"

    return SessionAggregate(
        session_key=session_key,
        driver_code=driver_code,
        laps_used=laps_used,
        avg_lap_time_s=avg_lap_time_s,
        mean_speed=mean_speed,
        max_speed=max_speed,
        full_throttle_pct=full_throttle_pct,
        heavy_brake_pct=heavy_brake_pct,
        coasting_pct=coasting_pct,
        aggression_score=float(aggression_score),
        braking_risk=float(braking_risk),
        style_tag=style_tag,
    )


# ---------- TOP-LEVEL PROFILE BUILDER ---------- #

def build_driver_profiles() -> Dict[str, DriverProfile]:
    """
    Loop over SESSIONS × DRIVERS and build profiles.
    """
    ensure_cache()
    profiles: Dict[str, DriverProfile] = {}

    for drv in DRIVERS:
        profiles[drv["code"]] = DriverProfile(
            driver_code=drv["code"],
            driver_name=drv["name"],
            sessions=[],
            overall={},
        )

    for sess_cfg in SESSIONS:
        print(
            f"\n=== Loading {sess_cfg['year']} {sess_cfg['event']} "
            f"{sess_cfg['session']} ==="
        )
        session = fastf1.get_session(
            sess_cfg["year"], sess_cfg["event"], sess_cfg["session"]
        )
        # This will fetch timing + telemetry from F1’s live timing servers
        session.load(laps=True, telemetry=True, weather=False)

        for drv in DRIVERS:
            code = drv["code"]
            agg = aggregate_session(session, code)
            if agg is None:
                print(f"  – No usable laps for {code} in this session")
                continue

            profiles[code].sessions.append(agg)
            print(
                f"  – {code}: style={agg.style_tag}, "
                f"aggr={agg.aggression_score:.2f}, "
                f"brakeRisk={agg.braking_risk:.2f}"
            )

    # Now compute overall stats per driver by averaging over sessions
    for code, profile in profiles.items():
        if not profile.sessions:
            continue

        df = pd.DataFrame([asdict(s) for s in profile.sessions])

        profile.overall = {
            "sessions_used": int(len(df)),
            "avg_lap_time_s": float(df["avg_lap_time_s"].mean()),
            "mean_speed": float(df["mean_speed"].mean()),
            "max_speed": float(df["max_speed"].max()),
            "full_throttle_pct": float(df["full_throttle_pct"].mean()),
            "heavy_brake_pct": float(df["heavy_brake_pct"].mean()),
            "coasting_pct": float(df["coasting_pct"].mean()),
            "aggression_score": float(df["aggression_score"].mean()),
            "braking_risk": float(df["braking_risk"].mean()),
        }

        # Majority style tag across sessions
        style_counts = df["style_tag"].value_counts()
        profile.overall["style_tag"] = str(style_counts.idxmax())

    return profiles


def save_profiles_to_json(
    profiles: Dict[str, DriverProfile],
    output_path: Path | None = None,
):
    """
    Save profiles into a JSON file for later use by your backend / RL.
    """
    if output_path is None:
        output_path = BASE_DIR / "driver_profiles.json"

    serialisable = {}
    for code, profile in profiles.items():
        serialisable[code] = {
            "driver_code": profile.driver_code,
            "driver_name": profile.driver_name,
            "overall": profile.overall,
            "sessions": [asdict(s) for s in profile.sessions],
        }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(serialisable, f, indent=2)

    print(f"\nSaved driver profiles to {output_path}")


def main():
    profiles = build_driver_profiles()
    save_profiles_to_json(profiles)


if __name__ == "__main__":
    main()
