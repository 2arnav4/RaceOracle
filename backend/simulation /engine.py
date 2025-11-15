"""
Engine module: Defines the SimulationEngine that orchestrates the simulation.
"""

import math
from simulation.world import World
from simulation.vehicle import Vehicle
from simulation.events import EventEngine


class SimulationEngine:
    """
    Main simulation engine that orchestrates the race simulation.

    Responsibilities:
    - Maintain World state
    - Execute per-step updates: observations, actions, physics, events
    - Track race progress and determine winners
    - Generate and return race results
    """

    def __init__(self, world, event_engine, vehicle_controllers):
        """
        Initialize the simulation engine.

        Args:
            world: World instance
            event_engine: EventEngine instance
            vehicle_controllers: Dict mapping vehicle_id -> controller instance
        """
        self.world = world
        self.event_engine = event_engine
        self.vehicle_controllers = vehicle_controllers

        # Race configuration
        self.target_laps = 3  # Number of laps to complete
        self.max_time = 600.0  # Maximum race duration in seconds

        # Race state
        self.is_race_active = False
        self.race_start_time = None

    def set_race_config(self, target_laps=3, max_time=600.0):
        """
        Configure race parameters.

        Args:
            target_laps: Number of laps required to finish
            max_time: Maximum race duration in seconds
        """
        self.target_laps = target_laps
        self.max_time = max_time

    def reset_race(self):
        """Reset all state for a new race."""
        self.world.reset()
        self.event_engine.reset()
        self.is_race_active = True
        self.race_start_time = 0.0

        # Initialize vehicles on the starting line (on the track centerline)
        for vehicle in self.world.get_all_vehicles():
            start_x, start_y = self.world.track.get_centerline_point(0.0)
            vehicle.x = start_x
            vehicle.y = start_y
            vehicle.speed = 0.0
            vehicle.heading = 0.0

        for controller in self.vehicle_controllers.values():
            controller.reset()

    def is_race_finished(self):
        """
        Check if the race should end.

        Race ends when:
        - All vehicles have finished (or timed out), OR
        - Max time reached

        Returns:
            True if race should end, False otherwise
        """
        if self.world.time_elapsed >= self.max_time:
            return True

        # Check if enough vehicles have finished (either DNF or completed race)
        vehicles = self.world.get_all_vehicles()
        finished_count = sum(1 for v in vehicles if v.is_finished)

        return finished_count == len(vehicles)

    def step(self):
        """
        Execute one simulation timestep.

        Steps:
        1. Fire scheduled events
        2. Generate random events
        3. For each vehicle:
           a. Build observation
           b. Get action from controller
           c. Update vehicle physics
           d. Update lap progress
           e. Record telemetry
        4. Check for crashes and engine failures
        5. Determine race completion
        6. Advance world time
        """
        # Fire scheduled and random events
        self.event_engine.fire_scheduled_events(self.world.time_elapsed, self.world)
        self.event_engine.generate_random_events(self.world.time_elapsed, self.world)

        # Get weather effects
        weather_effects = self.world.get_weather_effects()
        friction_mult = weather_effects.get("friction_multiplier", 1.0)
        weather_effect = weather_effects.get("visibility_multiplier", 1.0)

        # Update each vehicle
        for vehicle in self.world.get_all_vehicles():
            if vehicle.is_finished:
                continue

            # Build observation
            obs = vehicle.get_state()

            # Get action from controller
            controller = self.vehicle_controllers.get(vehicle.id)
            if controller is None:
                throttle, brake, steer = 0.0, 0.0, 0.0
            else:
                throttle, brake, steer = controller.get_action(obs)

            # Update physics
            vehicle.update_physics(
                self.world.dt,
                throttle,
                brake,
                steer,
                friction_mult=friction_mult,
                weather_effect=weather_effect,
            )

            # Update lap progress
            new_progress = self.world.track.progress_from_position(
                vehicle.x, vehicle.y
            )

            # Check for lap completion
            if self.world.track.is_lap_complete(new_progress, vehicle.lap_progress):
                vehicle.increment_lap()

            vehicle.update_lap_progress(new_progress)

            # Check if vehicle finished (completed target laps)
            if vehicle.lap_count >= self.target_laps and not vehicle.is_finished:
                vehicle.finish_race(
                    position=len([v for v in self.world.get_all_vehicles() if v.is_finished]) + 1,
                    time=self.world.time_elapsed,
                )

            # Check for crash due to control impairment (probabilistic)
            if not vehicle.is_finished and vehicle.is_control_impaired:
                # 0.3% chance per timestep when impaired (causes crashes but very rarely)
                import random
                if random.random() < 0.003:
                    vehicle.finish_race_dnf("CRASH", self.world.time_elapsed)
                    continue

            # Check for catastrophic engine failure (cumulative failure too long)
            if not vehicle.is_finished and vehicle.cumulative_engine_failure_time > 15.0:
                vehicle.finish_race_dnf("ENGINE_FAILURE", self.world.time_elapsed)
                continue

            # Record telemetry
            vehicle.record_telemetry(self.world.time_elapsed)

        # Check for timeout: mark remaining vehicles as DNF at max_time
        if self.world.time_elapsed >= self.max_time:
            for vehicle in self.world.get_all_vehicles():
                if not vehicle.is_finished:
                    vehicle.finish_race_dnf("TIMEOUT", self.world.time_elapsed)

        # Advance world time
        self.world.step()

    def run_episode(self):
        """
        Run a complete race episode until finish condition.

        Returns:
            Race results dict
        """
        self.reset_race()

        while not self.is_race_finished():
            self.step()

        return self.get_race_results()

    def get_race_results(self):
        """
        Compile and return race results.

        Returns:
            Dict with finishing_positions, lap_counts, times, telemetry, and events
        """
        vehicles = self.world.get_all_vehicles()

        # Sort by finish position (completions first, then DNFs)
        finished_vehicles = sorted(
            [v for v in vehicles if v.is_finished],
            key=lambda v: (v.finish_position is None, v.finish_time),
        )

        # Build results
        results = {
            "total_time": self.world.time_elapsed,
            "target_laps": self.target_laps,
            "finishing_positions": [],
            "dnf_vehicles": [],
            "events": self.event_engine.get_events_fired(),
        }

        # Add finished vehicles (winners)
        position = 1
        for vehicle in finished_vehicles:
            if vehicle.finish_position is not None:  # Completed the race
                results["finishing_positions"].append(
                    {
                        "position": vehicle.finish_position,
                        "vehicle_id": vehicle.id,
                        "vehicle_name": vehicle.name,
                        "finish_time": vehicle.finish_time,
                        "lap_count": vehicle.lap_count,
                        "telemetry_length": len(vehicle.telemetry_history),
                        "event_log": vehicle.event_log,
                    }
                )

        # Add DNF vehicles
        for vehicle in finished_vehicles:
            if vehicle.dnf_reason is not None:  # Did not finish
                results["dnf_vehicles"].append(
                    {
                        "vehicle_id": vehicle.id,
                        "vehicle_name": vehicle.name,
                        "dnf_reason": vehicle.dnf_reason,
                        "dnf_time": vehicle.finish_time,
                        "lap_count": vehicle.lap_count,
                        "lap_progress": vehicle.lap_progress,
                        "event_log": vehicle.event_log,
                    }
                )

        return results

    def __repr__(self):
        return (
            f"SimulationEngine(target_laps={self.target_laps}, "
            f"max_time={self.max_time}, vehicles={self.world.get_vehicle_count()})"
        )
