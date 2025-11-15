"""
Events module: Defines the EventEngine for applying scheduled and random events.
"""

import random


class Event:
    """Represents a single event."""

    def __init__(self, event_type, time, **kwargs):
        """
        Initialize an event.

        Args:
            event_type: Type of event (e.g., "RAIN_ON", "ENGINE_FAILURE")
            time: Simulation time when event occurs
            **kwargs: Additional event-specific parameters
        """
        self.type = event_type
        self.time = time
        self.params = kwargs
        self.has_fired = False

    def __repr__(self):
        return f"Event(type={self.type}, time={self.time}, params={self.params})"


class EventEngine:
    """
    Manages scheduled and random events during simulation.

    Scheduled events fire at predetermined times.
    Random events are generated based on configured probabilities.
    """

    def __init__(self):
        """Initialize the event engine."""
        self.scheduled_events = []  # List of Event objects
        self.random_event_config = {}  # Config for random event generation
        self.events_fired = []  # History of events that have fired

        # Default random event probabilities (per timestep)
        self.default_random_config = {
            "engine_failure_prob": 0.001,  # 0.1% chance per step
            "control_impairment_prob": 0.002,  # 0.2% chance per step
            "rain_on_prob": 0.005,  # 0.5% chance per step
            "rain_off_prob": 0.003,  # 0.3% chance per step
        }

    def add_scheduled_event(self, event_type, time, **kwargs):
        """
        Schedule an event to occur at a specific time.

        Args:
            event_type: Type of event
            time: Simulation time when event occurs
            **kwargs: Event-specific parameters
        """
        event = Event(event_type, time, **kwargs)
        self.scheduled_events.append(event)

    def set_random_event_config(self, config):
        """
        Configure random event probabilities.

        Args:
            config: Dict with keys like 'engine_failure_prob', 'rain_on_prob', etc.
        """
        self.random_event_config = {**self.default_random_config, **config}

    def fire_scheduled_events(self, current_time, world):
        """
        Check and fire any scheduled events that should occur at current time.

        Args:
            current_time: Current simulation time
            world: World instance to apply events to
        """
        for event in self.scheduled_events:
            if not event.has_fired and abs(event.time - current_time) < 0.01:
                # Fire the event
                self._apply_event(event, world)
                event.has_fired = True
                self.events_fired.append(
                    {"type": event.type, "time": current_time, "params": event.params}
                )

    def generate_random_events(self, current_time, world):
        """
        Generate and apply random events based on configured probabilities.

        Args:
            current_time: Current simulation time
            world: World instance to apply events to
        """
        config = self.random_event_config or self.default_random_config

        # Random rain event
        if random.random() < config.get("rain_on_prob", 0.0):
            world.set_weather(True)
            self.events_fired.append(
                {"type": "RAIN_ON", "time": current_time, "vehicle_id": None}
            )

        if random.random() < config.get("rain_off_prob", 0.0):
            world.set_weather(False)
            self.events_fired.append(
                {"type": "RAIN_OFF", "time": current_time, "vehicle_id": None}
            )

        # Random vehicle failures
        for vehicle in world.get_all_vehicles():
            if vehicle.is_finished:
                continue

            # Engine failure
            if random.random() < config.get("engine_failure_prob", 0.0):
                vehicle.apply_engine_failure(duration=random.uniform(2.0, 5.0))
                self.events_fired.append(
                    {
                        "type": "ENGINE_FAILURE",
                        "time": current_time,
                        "vehicle_id": vehicle.id,
                    }
                )

            # Control impairment
            if random.random() < config.get("control_impairment_prob", 0.0):
                vehicle.apply_control_impairment(duration=random.uniform(1.0, 3.0))
                self.events_fired.append(
                    {
                        "type": "CONTROL_IMPAIRMENT",
                        "time": current_time,
                        "vehicle_id": vehicle.id,
                    }
                )

    def _apply_event(self, event, world):
        """
        Apply an event's effects to the world and vehicles.

        Args:
            event: Event instance
            world: World instance
        """
        if event.type == "RAIN_ON":
            world.set_weather(True)

        elif event.type == "RAIN_OFF":
            world.set_weather(False)

        elif event.type == "ENGINE_FAILURE":
            vehicle_id = event.params.get("vehicle_id")
            if vehicle_id is not None:
                vehicle = world.get_vehicle(vehicle_id)
                if vehicle:
                    duration = event.params.get("duration", 5.0)
                    vehicle.apply_engine_failure(duration)

        elif event.type == "CONTROL_IMPAIRMENT":
            vehicle_id = event.params.get("vehicle_id")
            if vehicle_id is not None:
                vehicle = world.get_vehicle(vehicle_id)
                if vehicle:
                    duration = event.params.get("duration", 3.0)
                    vehicle.apply_control_impairment(duration)

    def get_events_fired(self):
        """Return the list of events that have fired during the simulation."""
        return self.events_fired

    def reset(self):
        """Reset the event engine for a new episode."""
        self.scheduled_events = []
        self.events_fired = []

    def __repr__(self):
        return f"EventEngine(scheduled_events={len(self.scheduled_events)})"
