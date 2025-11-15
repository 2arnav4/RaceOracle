from typing import List, Dict, Any
import math
import random
import time
from ..models import AgentState, SimulationState # <-- FIX APPLIED HERE

from .agents import SimpleRuleBasedAgent
from .aggressive_driver import AggressiveDriverAgent


class SimulationEngine:
    def __init__(
        self,
        track_points: List[Dict[str, float]],
        agent_configs: List[Dict[str, Any]],
        tick_dt: float = 0.1,
        max_laps: int = 5,
    ):
        self.track_points = track_points
        self.tick_dt = tick_dt
        self.max_laps = max_laps
        self.time = 0.0
        self.event_log: List[str] = []
        self.weather: str = "dry"

        self.agents: List[AgentState] = []
        self.agent_controllers = {}

        self._init_agents(agent_configs)

        self._last_weather_toggle = 0.0

    def _init_agents(self, agent_configs: List[Dict[str, Any]]) -> None:
        for cfg in agent_configs:
            agent_id = cfg["id"]
            color = cfg.get("color", "#00FFD1")
            personality = cfg.get("personality", "neutral")
            controller_type = cfg.get("controller", "rule_based")

            if controller_type == "aggressive":
                controller = AggressiveDriverAgent(agent_id, color)
            elif controller_type == "rl":
                controller = SimpleRuleBasedAgent(agent_id, color, "neutral")
            else:
                controller = SimpleRuleBasedAgent(agent_id, color, personality)

            self.agent_controllers[agent_id] = controller

            # Start at first segment
            state = AgentState(
                id=agent_id,
                color=color,
                x=self.track_points[0]["x"],
                y=self.track_points[0]["y"],
                heading=0.0,
                speed=0.0,
                lap=0,
                status="RACING",
                segment_index=0,
                segment_progress=0.0,
            )
            self.agents.append(state)

    def _segment_length(self, i: int) -> float:
        p1 = self.track_points[i]
        p2 = self.track_points[(i + 1) % len(self.track_points)]
        return math.dist((p1["x"], p1["y"]), (p2["x"], p2["y"]))

    def _interpolate_position(self, seg_idx: int, t: float) -> (float, float):
        p1 = self.track_points[seg_idx]
        p2 = self.track_points[(seg_idx + 1) % len(self.track_points)]
        x = p1["x"] + (p2["x"] - p1["x"]) * t
        y = p1["y"] + (p2["y"] - p1["y"]) * t
        return x, y

    def _heading_from_segment(self, seg_idx: int) -> float:
        p1 = self.track_points[seg_idx]
        p2 = self.track_points[(seg_idx + 1) % len(self.track_points)]
        angle_rad = math.atan2(p2["y"] - p1["y"], p2["x"] - p1["x"])
        return math.degrees(angle_rad)

    def step(self) -> SimulationState:
        self.time += self.tick_dt

        # Random weather toggle every ~30s
        if self.time - self._last_weather_toggle > 30.0:
            if random.random() < 0.2:
                self.weather = "wet" if self.weather == "dry" else "dry"
                self._last_weather_toggle = self.time
                self.event_log.append(
                    f"[t={self.time:.1f}s] Weather changed to {self.weather.upper()}"
                )

        for i, agent in enumerate(self.agents):
            if agent.status != "RACING":
                continue

            controller = self.agent_controllers[agent.id]

            obs = {
                "speed": agent.speed,
                "lap": agent.lap,
                "segment_index": agent.segment_index,
                "segment_progress": agent.segment_progress,
                "weather": self.weather,
            }

            action = controller.choose_action(obs)
            throttle = action["throttle"]
            brake = action["brake"]

            # Very simple longitudinal dynamics
            accel = 8.0 * throttle - 10.0 * brake  # m/s^2-ish
            agent.speed = max(0.0, min(260.0, agent.speed + accel * self.tick_dt))

            # Convert speed km/h ~> "track units" (completely fake scaling)
            speed_units = agent.speed * 0.01

            seg_len = self._segment_length(agent.segment_index)
            dist_advance = speed_units * self.tick_dt
            seg_advance = dist_advance / max(seg_len, 1e-6)

            agent.segment_progress += seg_advance

            while agent.segment_progress >= 1.0:
                agent.segment_progress -= 1.0
                agent.segment_index = (agent.segment_index + 1) % len(
                    self.track_points
                )
                # Completed a lap when wrapping around to first segment
                if agent.segment_index == 0:
                    agent.lap += 1
                    self.event_log.append(
                        f"[t={self.time:.1f}s] {agent.id} completed lap {agent.lap}"
                    )
                    if agent.lap >= self.max_laps:
                        agent.status = "FINISHED"
                        self.event_log.append(
                            f"[t={self.time:.1f}s] {agent.id} finished the race"
                        )
                        break

            agent.x, agent.y = self._interpolate_position(
                agent.segment_index, agent.segment_progress
            )
            agent.heading = self._heading_from_segment(agent.segment_index)

            # Random mechanical failure
            if random.random() < 0.0005:
                agent.status = "DNF"
                self.event_log.append(
                    f"[t={self.time:.1f}s] {agent.id} retired (mechanical failure)"
                )

        return SimulationState(time=self.time, agents=self.agents, event_log=self.event_log[-50:])

    def reset(self) -> SimulationState:
        self.time = 0.0
        self.weather = "dry"
        self.event_log = ["[t=0.0s] Simulation reset"]
        # Re-init agents with same config
        configs = []
        for agent in self.agents:
            configs.append(
                {
                    "id": agent.id,
                    "color": agent.color,
                    "personality": "neutral",
                    "controller": "rule_based",
                }
            )
        self.agents.clear()
        self.agent_controllers.clear()
        self._init_agents(configs)
        return SimulationState(time=self.time, agents=self.agents, event_log=self.event_log)
