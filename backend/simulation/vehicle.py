"""
Vehicle module: Defines the Vehicle class representing a single racing car.
"""


class Vehicle:
    """
    Represents a single vehicle (car) in the simulation.
    
    Maintains physics state (position, speed, heading) and race progress tracking.
    Applies simple physics: speed changes via throttle/brake, heading via steering,
    and friction/weather effects.
    """

    def __init__(
        self,
        vehicle_id,
        name="Vehicle",
        team="",
        max_speed=50.0,
        max_acceleration=10.0,
        max_deceleration=15.0,
        max_steer_rate=0.5,
    ):
        """
        Initialize a vehicle.

        Args:
            vehicle_id: Unique identifier for this vehicle
            name: Display name
            team: Team name (for team-based races)
            max_speed: Maximum speed in m/s (default: 50.0)
            max_acceleration: Max acceleration in m/s² (default: 10.0)
            max_deceleration: Max deceleration in m/s² (default: 15.0)
            max_steer_rate: Max steering rate in rad/s (default: 0.5)
        """
        self.id = vehicle_id
        self.name = name
        self.team = team

        # Physics limits
        self.max_speed = max_speed
        self.max_acceleration = max_acceleration
        self.max_deceleration = max_deceleration
        self.max_steer_rate = max_steer_rate

        # Physics state
        self.x = 0.0
        self.y = 0.0
        self.speed = 0.0  # m/s
        self.heading = 0.0  # radians, 0 = +x direction

        # Race tracking
        self.lap_progress = 0.0  # Distance along centerline
        self.lap_count = 0  # Number of completed laps
        self.is_finished = False
        self.finish_time = None
        self.finish_position = None
        self.dnf_reason = None  # Reason for did-not-finish (if applicable)

        # Failure state
        self.is_engine_failed = False
        self.is_control_impaired = False
        self.failure_recovery_time = 0.0
        self.cumulative_engine_failure_time = 0.0  # Track total failure time

        # Telemetry history for analysis
        self.telemetry_history = []  # List of state dicts at each step
        self.event_log = []  # List of events that occurred to this vehicle

    def reset(self):
        """Reset vehicle state for a new episode."""
        self.x = 0.0
        self.y = 0.0
        self.speed = 0.0
        self.heading = 0.0
        self.lap_progress = 0.0
        self.lap_count = 0
        self.is_finished = False
        self.finish_time = None
        self.finish_position = None
        self.dnf_reason = None
        self.is_engine_failed = False
        self.is_control_impaired = False
        self.failure_recovery_time = 0.0
        self.cumulative_engine_failure_time = 0.0
        self.telemetry_history = []
        self.event_log = []

    def update_physics(
        self, dt, throttle, brake, steer, friction_mult=1.0, weather_effect=1.0
    ):
        """
        Update vehicle physics for one timestep.

        Args:
            dt: Time delta in seconds
            throttle: Throttle input in [0, 1] (0 = no throttle, 1 = full)
            brake: Brake input in [0, 1] (0 = no brake, 1 = full)
            steer: Steering input in [-1, 1] (-1 = left, 1 = right)
            friction_mult: Multiplier for friction (1.0 = normal, >1 = more friction)
            weather_effect: Multiplier for weather effects on max speed (1.0 = clear, <1 = rain/fog)
        """
        # Handle engine failure
        if self.is_engine_failed:
            throttle = 0.0
            self.cumulative_engine_failure_time += dt
            self.failure_recovery_time -= dt
            if self.failure_recovery_time <= 0:
                self.is_engine_failed = False
                self.event_log.append(
                    {"type": "ENGINE_RECOVERED", "time": dt}
                )

        # Clamp inputs to valid ranges
        throttle = max(0.0, min(1.0, throttle))
        brake = max(0.0, min(1.0, brake))
        steer = max(-1.0, min(1.0, steer))

        # Calculate net acceleration
        accel_from_throttle = throttle * self.max_acceleration
        accel_from_brake = -brake * self.max_deceleration

        net_acceleration = accel_from_throttle + accel_from_brake

        # Apply friction (always acts opposite to motion)
        friction_deceleration = 0.5 * friction_mult
        if self.speed > 0:
            net_acceleration -= friction_deceleration

        # Update speed
        self.speed += net_acceleration * dt

        # Apply weather effect to max speed
        effective_max_speed = self.max_speed * weather_effect
        self.speed = max(0.0, min(self.speed, effective_max_speed))

        # Handle control impairment
        if self.is_control_impaired:
            steer *= 0.5  # Reduce steering effectiveness
            self.failure_recovery_time -= dt
            if self.failure_recovery_time <= 0:
                self.is_control_impaired = False
                self.event_log.append(
                    {"type": "CONTROL_RECOVERED", "time": dt}
                )

        # Update heading (turning rate proportional to speed and steering input)
        steer_factor = 0.1  # Converts [steer * speed] to angular change
        heading_change = steer * self.speed * steer_factor * dt
        self.heading += heading_change

        # Update position
        import math

        self.x += self.speed * math.cos(self.heading) * dt
        self.y += self.speed * math.sin(self.heading) * dt

    def update_lap_progress(self, new_progress):
        """
        Update lap progress and detect lap completions.

        Args:
            new_progress: New progress value from track (distance along centerline)
        """
        old_progress = self.lap_progress
        self.lap_progress = new_progress

        # Detect lap completion (progress wraps around)
        # This is typically detected by the track's is_lap_complete() method
        # but we keep a simple flag here. The engine will call increment_lap()
        # when a lap is detected.

    def increment_lap(self):
        """Record that the vehicle has completed another lap."""
        self.lap_count += 1
        self.event_log.append(
            {"type": "LAP_COMPLETE", "lap": self.lap_count}
        )

    def apply_engine_failure(self, duration=5.0):
        """
        Apply an engine failure that reduces throttle effectiveness.

        Args:
            duration: How long the failure lasts in seconds
        """
        if not self.is_engine_failed:
            self.is_engine_failed = True
            self.failure_recovery_time = duration
            self.event_log.append(
                {"type": "ENGINE_FAILURE", "duration": duration}
            )

    def apply_control_impairment(self, duration=3.0):
        """
        Apply a control impairment (e.g., loose steering) that reduces steering effectiveness.

        Args:
            duration: How long the impairment lasts in seconds
        """
        if not self.is_control_impaired:
            self.is_control_impaired = True
            self.failure_recovery_time = duration
            self.event_log.append(
                {"type": "CONTROL_IMPAIRMENT", "duration": duration}
            )

    def get_state(self):
        """
        Return the current vehicle state as an observation dict.

        Used by controllers to make decisions.

        Returns:
            Dict with current state information
        """
        return {
            "vehicle_id": self.id,
            "x": self.x,
            "y": self.y,
            "speed": self.speed,
            "heading": self.heading,
            "lap_progress": self.lap_progress,
            "lap_count": self.lap_count,
            "is_finished": self.is_finished,
            "is_engine_failed": self.is_engine_failed,
            "is_control_impaired": self.is_control_impaired,
            "dnf_reason": self.dnf_reason,
        }

    def record_telemetry(self, timestamp):
        """
        Record current state to telemetry history.

        Args:
            timestamp: Current simulation time
        """
        state = self.get_state()
        state["timestamp"] = timestamp
        self.telemetry_history.append(state)

    def get_telemetry(self):
        """Return the telemetry history for this vehicle."""
        return self.telemetry_history

    def finish_race(self, position, time):
        """
        Mark the vehicle as finished (crossed finish line).

        Args:
            position: Final position (1st, 2nd, etc.)
            time: Time when the vehicle finished
        """
        self.is_finished = True
        self.finish_position = position
        self.finish_time = time
        self.event_log.append(
            {"type": "RACE_FINISHED", "position": position, "time": time}
        )

    def finish_race_dnf(self, reason, time):
        """
        Mark the vehicle as did-not-finish with a reason.

        Args:
            reason: String reason for DNF (e.g., "CRASH", "ENGINE_FAILURE", "TIMEOUT")
            time: Time when the vehicle was marked as DNF
        """
        self.is_finished = True
        self.dnf_reason = reason
        self.finish_time = time
        self.event_log.append(
            {"type": "RACE_DNF", "reason": reason, "time": time}
        )

    def __repr__(self):
        return (
            f"Vehicle(id={self.id}, name={self.name}, speed={self.speed:.2f}, "
            f"lap={self.lap_count}, progress={self.lap_progress:.2f})"
        )
