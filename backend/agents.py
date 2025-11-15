from abc import ABC, abstractmethod
from typing import Dict, Any
import random


class BaseAgent(ABC):
    def __init__(self, agent_id: str, color: str, personality: str = "neutral"):
        self.id = agent_id
        self.color = color
        self.personality = personality

    @abstractmethod
    def choose_action(self, obs: Dict[str, Any]) -> Dict[str, float]:
        """
        obs: {
          'speed': float,
          'lap': int,
          'segment_index': int,
          'segment_progress': float,
          'weather': str,
        }
        returns: {'throttle': 0..1, 'brake': 0..1}
        """
        ...


class SimpleRuleBasedAgent(BaseAgent):
    """
    Very simple heuristic driver.
    personality: 'aggressive', 'cautious', 'neutral'
    """

    def choose_action(self, obs: Dict[str, Any]) -> Dict[str, float]:
        speed = obs["speed"]
        segment_progress = obs["segment_progress"]
        weather = obs.get("weather", "dry")

        # Base target speeds by personality
        if self.personality == "aggressive":
            target_speed = 230.0
        elif self.personality == "cautious":
            target_speed = 180.0
        else:
            target_speed = 200.0

        # Slow down slightly in the middle of segments (fake corners)
        if 0.3 < segment_progress < 0.7:
            target_speed *= 0.85

        # Weather effect
        if weather == "wet":
            target_speed *= 0.8

        throttle = 0.0
        brake = 0.0

        if speed < target_speed - 5:
            throttle = 1.0
        elif speed > target_speed + 5:
            brake = 1.0
        else:
            throttle = 0.3

        # Add some noise so different agents behave differently
        throttle = max(0.0, min(1.0, throttle + random.uniform(-0.05, 0.05)))
        brake = max(0.0, min(1.0, brake + random.uniform(-0.05, 0.05)))

        return {"throttle": throttle, "brake": brake}


class RLAgent(BaseAgent):
    """
    Placeholder for RL-controlled agent – you can plug in a trained policy later.
    """

    def __init__(self, agent_id: str, color: str, policy=None):
        super().__init__(agent_id, color, personality="rl")
        self.policy = policy

    def choose_action(self, obs: Dict[str, Any]) -> Dict[str, float]:
        if self.policy is None:
            # fallback to neutral rule-based behavior
            neutral = SimpleRuleBasedAgent(self.id, self.color, "neutral")
            return neutral.choose_action(obs)
        # Example shape – adapt when you have a real model
        return self.policy(obs)
