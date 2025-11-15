"""
MonteCarloRunner module: Runs multiple episodes and aggregates statistics.
"""

from simulation.world import World
from simulation.vehicle import Vehicle
from simulation.events import EventEngine
from simulation.engine import SimulationEngine


class MonteCarloRunner:
    """
    Runs multiple race episodes and collects aggregate statistics.

    Supports different scenarios with different vehicle configurations,
    controllers, and event schedules.
    """

    def __init__(self, scenario):
        """
        Initialize the runner with a scenario configuration.

        Args:
            scenario: Dict containing:
                - 'track_radius': Track radius (default: 100.0)
                - 'dt': Simulation timestep (default: 0.05)
                - 'target_laps': Laps per race (default: 3)
                - 'max_time': Max race duration (default: 600.0)
                - 'vehicles': List of vehicle configs
                  Each vehicle config is a dict:
                  - 'id': unique identifier
                  - 'name': display name
                  - 'controller': controller instance
                  - 'vehicle_params': optional dict with max_speed, etc.
                - 'event_config': dict with scheduled and random event configs
                  - 'random_events': dict of probabilities
                  - 'scheduled_events': list of event dicts
        """
        self.scenario = scenario
        self.results = []  # List of race results from all episodes

    def run_many(self, num_episodes=10):
        """
        Run multiple race episodes.

        Args:
            num_episodes: Number of episodes to run

        Returns:
            Aggregated results dict
        """
        self.results = []

        for episode in range(num_episodes):
            result = self._run_single_episode(episode)
            self.results.append(result)

        return self._aggregate_results(num_episodes)

    def _run_single_episode(self, episode_number):
        """
        Run a single race episode.

        Args:
            episode_number: Episode index (0-based)

        Returns:
            Race results dict
        """
        # Create world
        track_radius = self.scenario.get("track_radius", 100.0)
        dt = self.scenario.get("dt", 0.05)
        world = World(track_radius=track_radius, dt=dt)

        # Create event engine and configure
        event_engine = EventEngine()
        event_config = self.scenario.get("event_config", {})

        if "random_events" in event_config:
            event_engine.set_random_event_config(event_config["random_events"])

        if "scheduled_events" in event_config:
            for event_spec in event_config["scheduled_events"]:
                event_engine.add_scheduled_event(**event_spec)

        # Create vehicles and get controllers
        vehicle_controllers = {}
        vehicle_configs = self.scenario.get("vehicles", [])
        vehicle_teams = {}  # Map vehicle_id -> team name

        for vehicle_config in vehicle_configs:
            vehicle_id = vehicle_config.get("id")
            name = vehicle_config.get("name", f"Vehicle_{vehicle_id}")
            team = vehicle_config.get("team", "")
            controller = vehicle_config.get("controller")

            # Optional vehicle parameters
            vehicle_params = vehicle_config.get("vehicle_params", {})
            vehicle = Vehicle(vehicle_id, name=name, team=team, **vehicle_params)
            vehicle_teams[vehicle_id] = team

            world.add_vehicle(vehicle)
            vehicle_controllers[vehicle_id] = controller

        # Create simulation engine
        engine = SimulationEngine(world, event_engine, vehicle_controllers)
        engine.set_race_config(
            target_laps=self.scenario.get("target_laps", 3),
            max_time=self.scenario.get("max_time", 600.0),
        )

        # Run the race
        results = engine.run_episode()
        results["episode"] = episode_number
        results["vehicle_teams"] = vehicle_teams

        return results

    def _aggregate_results(self, num_episodes):
        """
        Aggregate results across all episodes.

        Args:
            num_episodes: Number of episodes run

        Returns:
            Aggregated results dict
        """
        aggregated = {
            "num_episodes": num_episodes,
            "results_per_episode": self.results,
            "statistics": self._compute_statistics(),
        }

        return aggregated

    def _compute_statistics(self):
        """
        Compute aggregate statistics across all episodes.

        Returns:
            Dict with statistical summaries
        """
        stats = {
            "vehicles": {},  # Per-vehicle statistics
            "overall": {},
            "dnf_reasons": {},  # Aggregate DNF reasons
        }

        # Collect vehicle IDs from all episodes
        all_vehicle_ids = set()
        for result in self.results:
            for finish in result.get("finishing_positions", []):
                all_vehicle_ids.add(finish["vehicle_id"])
            for dnf in result.get("dnf_vehicles", []):
                all_vehicle_ids.add(dnf["vehicle_id"])

        # Compute per-vehicle statistics
        for vehicle_id in all_vehicle_ids:
            finish_times = []
            positions = []
            lap_counts = []
            finish_count = 0
            dnf_count = 0
            dnf_by_reason = {}

            for result in self.results:
                # Check if finished (completed race)
                for finish in result.get("finishing_positions", []):
                    if finish["vehicle_id"] == vehicle_id:
                        finish_times.append(finish["finish_time"])
                        positions.append(finish["position"])
                        lap_counts.append(finish["lap_count"])
                        finish_count += 1
                        break
                else:
                    # Check if DNF
                    for dnf in result.get("dnf_vehicles", []):
                        if dnf["vehicle_id"] == vehicle_id:
                            lap_counts.append(dnf["lap_count"])
                            dnf_count += 1
                            reason = dnf["dnf_reason"]
                            dnf_by_reason[reason] = dnf_by_reason.get(reason, 0) + 1
                            break

            stats["vehicles"][vehicle_id] = {
                "finish_count": finish_count,
                "dnf_count": dnf_count,
                "finish_rate": finish_count / len(self.results),
                "dnf_rate": dnf_count / len(self.results),
                "avg_finish_time": sum(finish_times) / len(finish_times)
                if finish_times
                else None,
                "min_finish_time": min(finish_times) if finish_times else None,
                "max_finish_time": max(finish_times) if finish_times else None,
                "avg_position": sum(positions) / len(positions) if positions else None,
                "avg_lap_count": sum(lap_counts) / len(lap_counts)
                if lap_counts
                else 0,
                "wins": sum(1 for p in positions if p == 1),
                "dnf_reasons": dnf_by_reason,
            }

        # Aggregate DNF reasons across all episodes
        for result in self.results:
            for dnf in result.get("dnf_vehicles", []):
                reason = dnf["dnf_reason"]
                stats["dnf_reasons"][reason] = stats["dnf_reasons"].get(reason, 0) + 1

        # Compute overall statistics
        total_time_values = [r.get("total_time", 0) for r in self.results]
        total_dnf = sum(len(r.get("dnf_vehicles", [])) for r in self.results)
        total_finishes = sum(
            len(r.get("finishing_positions", [])) for r in self.results
        )

        stats["overall"] = {
            "avg_race_time": sum(total_time_values) / len(total_time_values),
            "min_race_time": min(total_time_values),
            "max_race_time": max(total_time_values),
            "total_events": sum(len(r.get("events", [])) for r in self.results),
            "total_finishes": total_finishes,
            "total_dnf": total_dnf,
            "dnf_rate": total_dnf / (total_finishes + total_dnf)
            if (total_finishes + total_dnf) > 0
            else 0,
        }

        return stats

    def get_results(self):
        """Return all race results collected so far."""
        return self.results

    def print_summary(self):
        """Print a human-readable summary of results with team and driver statistics."""
        if not self.results:
            print("No results to display. Run run_many() first.")
            return

        aggregated = self._aggregate_results(len(self.results))
        stats = aggregated["statistics"]

        # Build team statistics from vehicle stats
        team_stats = {}
        for vehicle_id, v_stats in stats["vehicles"].items():
            # Find team from scenario
            team_name = None
            for vehicle_config in self.scenario.get("vehicles", []):
                if vehicle_config.get("id") == vehicle_id:
                    team_name = vehicle_config.get("team", "Unknown")
                    break
            
            if team_name and team_name not in team_stats:
                team_stats[team_name] = {
                    "vehicles": [],
                    "combined_finish_count": 0,
                    "combined_dnf_count": 0,
                    "avg_finish_time": [],
                    "positions": [],
                    "wins": 0,
                }
            
            if team_name:
                team_stats[team_name]["vehicles"].append(vehicle_id)
                team_stats[team_name]["combined_finish_count"] += v_stats["finish_count"]
                team_stats[team_name]["combined_dnf_count"] += v_stats["dnf_count"]
                if v_stats["avg_finish_time"] is not None:
                    team_stats[team_name]["avg_finish_time"].append(v_stats["avg_finish_time"])
                team_stats[team_name]["wins"] += v_stats["wins"]

        print("=" * 80)
        print("MONTE CARLO SIMULATION RESULTS")
        print("=" * 80)
        print(f"Episodes run: {aggregated['num_episodes']}")
        print()

        # Print team statistics first
        print("TEAM STATISTICS (pairs of drivers):")
        print("-" * 80)
        for team_name in sorted(team_stats.keys()):
            t_stats = team_stats[team_name]
            avg_time = sum(t_stats["avg_finish_time"]) / len(t_stats["avg_finish_time"]) if t_stats["avg_finish_time"] else None
            finish_count = t_stats["combined_finish_count"]
            dnf_count = t_stats["combined_dnf_count"]
            finish_rate = finish_count / (finish_count + dnf_count) if (finish_count + dnf_count) > 0 else 0
            
            print(f"\n{team_name}:")
            print(f"  Drivers: {t_stats['vehicles']}")
            print(f"  Combined Finishes: {finish_count}, DNF: {dnf_count}")
            print(f"  Finish Rate: {finish_rate:.1%}")
            if avg_time:
                print(f"  Avg Finish Time: {avg_time:.2f}s")
            print(f"  Team Wins: {t_stats['wins']}")

        print()
        print("INDIVIDUAL DRIVER STATISTICS:")
        print("-" * 80)
        for vehicle_id in sorted(stats["vehicles"].keys()):
            vehicle_stats = stats["vehicles"][vehicle_id]
            # Find vehicle name
            vehicle_name = f"Vehicle {vehicle_id}"
            for vehicle_config in self.scenario.get("vehicles", []):
                if vehicle_config.get("id") == vehicle_id:
                    vehicle_name = vehicle_config.get("name", f"Vehicle {vehicle_id}")
                    break
            
            print(f"\n{vehicle_name}:")
            print(f"  Finish Rate: {vehicle_stats['finish_rate']:.1%}")
            print(f"  DNF Rate: {vehicle_stats['dnf_rate']:.1%}")
            if vehicle_stats['dnf_reasons']:
                print(f"  DNF Reasons: {vehicle_stats['dnf_reasons']}")
            if vehicle_stats['avg_finish_time'] is not None:
                print(f"  Avg Finish Time: {vehicle_stats['avg_finish_time']:.2f}s")
            if vehicle_stats['avg_position'] is not None:
                print(f"  Avg Position: {vehicle_stats['avg_position']:.2f}")
            print(f"  Wins: {vehicle_stats['wins']}")
            print(f"  Avg Lap Count: {vehicle_stats['avg_lap_count']:.2f}")

        print()
        print("OVERALL STATISTICS:")
        print("-" * 80)
        overall = stats["overall"]
        print(f"Total Finishes: {overall['total_finishes']}")
        print(f"Total DNF: {overall['total_dnf']}")
        print(f"Overall DNF Rate: {overall['dnf_rate']:.1%}")
        print(f"Avg Race Time: {overall['avg_race_time']:.2f}s")
        print(f"Min Race Time: {overall['min_race_time']:.2f}s")
        print(f"Max Race Time: {overall['max_race_time']:.2f}s")
        print(f"Total Events Fired: {overall['total_events']}")

        if stats["dnf_reasons"]:
            print()
            print("DNF REASONS BREAKDOWN:")
            print("-" * 80)
            for reason, count in sorted(
                stats["dnf_reasons"].items(), key=lambda x: x[1], reverse=True
            ):
                percentage = (count / overall['total_dnf'] * 100) if overall['total_dnf'] > 0 else 0
                print(f"  {reason}: {count} ({percentage:.1f}%)")

        print("=" * 80)

    def __repr__(self):
        return f"MonteCarloRunner(episodes={len(self.results)})"
