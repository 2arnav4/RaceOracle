import json
import random
import math
from pathlib import Path
from simulation.controllers import BaseController


PROFILE_PATH = (
    Path(__file__).resolve().parents[2]
    / "driver_profiles"
    / "driver_profiles.json"
)


class DriverStyleController(BaseController):
    """AI Controller that behaves based on real driver style + dynamic conditions."""

    def __init__(self, driver_code: str, track_radius=100.0):
        super().__init__(name=f"DriverStyle-{driver_code}")
        self.driver_code = driver_code
        self.track_radius = track_radius

        self.profile = self._load_profile()

        # base values from FastF1 stats
        self.base_speed = self._map_target_speed()
        self.aggression = self.profile["overall"]["aggression_score"]
        self.brake_bias = self.profile["overall"]["braking_risk"]
        self.coast_bias = self.profile["overall"]["coasting_pct"]

        # dynamic game state values
        self.tire_wear = 0.0
        self.confidence = 1.0     # drop on crashes / events
        self.fuel_penalty = 1.0   # high early, drops later

    def _load_profile(self):
        with open(PROFILE_PATH, "r") as f:
            return json.load(f)[self.driver_code]

    def _map_target_speed(self):
        max_kmh = self.profile["overall"]["max_speed"]
        return min(max_kmh / 8, 60)

    # ------------ DYNAMIC ADAPTATION ---------------
    def _update_state(self, obs):
        """Modify driving characteristics over time / conditions."""
        lap_progress = obs.get("lap_progress", 0)
        lap_count = obs.get("lap_count", 1)

        # Tire degradation increases linearly per lap
        self.tire_wear = min(1.0, lap_count * 0.12)

        # Reduce willingness to take risks with worn tires
        self.aggression = max(0.4, self.profile["overall"]["aggression_score"] - (self.tire_wear * 0.25))

        # Fuel load decreases → slight pace boost
        self.fuel_penalty = max(0.7, 1 - (lap_count * 0.05))

        # Confidence dynamics: more speed → stabilizes handling
        if obs.get("speed", 0) > self.base_speed * 0.9:
            self.confidence = min(1.2, self.confidence + 0.01)
        else:
            self.confidence = max(0.8, self.confidence - 0.002)

    # ------------ MAIN LOGIC ---------------
    def get_action(self, obs):
        self._update_state(obs)

        x, y = obs.get("x", 0), obs.get("y", 0)
        speed = obs.get("speed", 0)

        # SPEED TARGET CHANGES WITH RACE CONDITIONS
        dynamic_speed_target = self.base_speed * self.fuel_penalty * self.confidence

        # SPEED CONTROL
        if speed < dynamic_speed_target:
            throttle = min(1.0, self.aggression + 0.15)
            brake = 0.0
        else:
            throttle = max(0, (1 - self.brake_bias) * self.confidence)
            brake = min(1.0, self.brake_bias + self.tire_wear * 0.3)

        # STEERING CONTROL W/ REAL DRIVER VARIANCE
        dist = math.sqrt(x**2 + y**2)
        steer_err = (dist - self.track_radius)

        steer = (
            -steer_err / self.track_radius
            * (0.15 + self.aggression * 0.25)
            * (1 - self.tire_wear * 0.3)
        )

        # Realistic driver "jitter"
        steer += random.uniform(-0.02, 0.02) * (0.5 + self.coast_bias)

        return (
            round(throttle, 3),
            round(brake, 3),
            max(-1, min(1, round(steer, 3)))
        )
