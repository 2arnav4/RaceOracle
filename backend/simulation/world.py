"""
World module: Defines the World class that manages simulation state.
"""

from simulation.track import Track


class Weather:
    """Simple weather state container."""

    def __init__(self):
        """Initialize clear weather conditions."""
        self.is_raining = False
        self.friction_multiplier = 1.0  # 1.0 = normal, >1 = slippery
        self.visibility_multiplier = 1.0  # 1.0 = clear, <1 = fog

    def set_rain(self, is_raining):
        """
        Set rain state.

        Args:
            is_raining: True if raining, False if clear
        """
        self.is_raining = is_raining
        if is_raining:
            self.friction_multiplier = 1.5
            self.visibility_multiplier = 0.8
        else:
            self.friction_multiplier = 1.0
            self.visibility_multiplier = 1.0

    def get_effects(self):
        """
        Return current weather effects as a dict.

        Returns:
            Dict with friction_multiplier and visibility_multiplier
        """
        return {
            "is_raining": self.is_raining,
            "friction_multiplier": self.friction_multiplier,
            "visibility_multiplier": self.visibility_multiplier,
        }

    def __repr__(self):
        return (
            f"Weather(raining={self.is_raining}, "
            f"friction={self.friction_multiplier:.1f})"
        )


class World:
    """
    Represents the simulation world.

    Manages the track, all vehicles, time, and environmental state (weather).
    """

    def __init__(self, track_radius=100.0, dt=0.05):
        """
        Initialize the world.

        Args:
            track_radius: Radius of the circular track (default: 100.0 meters)
            dt: Simulation timestep (default: 0.05 seconds)
        """
        self.track = Track(radius=track_radius)
        self.dt = dt
        self.time_elapsed = 0.0

        self.vehicles = {}  # Dict mapping vehicle_id -> Vehicle
        self.weather = Weather()

    def add_vehicle(self, vehicle):
        """
        Add a vehicle to the world.

        Args:
            vehicle: Vehicle instance to add
        """
        self.vehicles[vehicle.id] = vehicle

    def get_vehicle(self, vehicle_id):
        """
        Get a vehicle by ID.

        Args:
            vehicle_id: The ID of the vehicle to retrieve

        Returns:
            Vehicle instance or None if not found
        """
        return self.vehicles.get(vehicle_id)

    def get_all_vehicles(self):
        """Return a list of all vehicles in the world."""
        return list(self.vehicles.values())

    def get_vehicle_count(self):
        """Return the number of vehicles in the world."""
        return len(self.vehicles)

    def set_weather(self, is_raining):
        """
        Set weather conditions.

        Args:
            is_raining: True for rain, False for clear conditions
        """
        self.weather.set_rain(is_raining)

    def get_weather_effects(self):
        """
        Get current weather effects.

        Returns:
            Dict with friction_multiplier and visibility_multiplier
        """
        return self.weather.get_effects()

    def step(self, dt=None):
        """
        Advance the world time by one timestep.

        Args:
            dt: Time delta (default: uses self.dt)
        """
        if dt is None:
            dt = self.dt

        self.time_elapsed += dt

    def reset(self):
        """Reset the world state for a new episode."""
        self.time_elapsed = 0.0
        self.weather = Weather()

        # Reset all vehicles
        for vehicle in self.vehicles.values():
            vehicle.reset()

    def get_state(self):
        """
        Return the current state of the entire world.

        Returns:
            Dict with time, weather, and vehicle info
        """
        vehicle_states = []
        for vehicle in self.vehicles.values():
            state = vehicle.get_state()
            vehicle_states.append(state)

        return {
            "time_elapsed": self.time_elapsed,
            "dt": self.dt,
            "weather": self.weather.get_effects(),
            "vehicles": vehicle_states,
            "track": {
                "radius": self.track.radius,
                "lap_distance": self.track.get_lap_distance(),
            },
        }

    def is_vehicle_crashed(self, vehicle):
        """
        Check if a vehicle has gone off-track (crashed).

        A vehicle crashes if its distance from the track centerline exceeds bounds.
        Using a lenient threshold to only catch severe off-track situations.

        Args:
            vehicle: Vehicle instance

        Returns:
            True if vehicle is severely off-track, False otherwise
        """
        distance_to_centerline = self.track.get_distance_to_centerline(
            vehicle.x, vehicle.y
        )

        # Allow 45 meters deviation from centerline before crash (reasonable for high-speed racing)
        crash_threshold = 45.0

        return distance_to_centerline > crash_threshold

    def __repr__(self):
        return (
            f"World(time={self.time_elapsed:.2f}s, "
            f"vehicles={len(self.vehicles)}, "
            f"weather={self.weather})"
        )
