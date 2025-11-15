import random
from typing import Dict

from backend.models import AgentState


class AggressiveDriverAgent:
    """
    Represents a high-risk aggressive driver.
    Behaviors:
      - Faster acceleration
      - Harder braking
      - Random lane deviations
      - Higher chance of overshooting corners
    """

    def __init__(self, agent_id: str, color: str = "#FF2D2D"):
        self.id = agent_id
        self.color = color

        # Base driving parameters
        self.speed = random.uniform(18, 28)  # m/s (65–100 km/h)
        self.heading = random.uniform(0, 360)
        self.x = random.uniform(200, 400)
        self.y = random.uniform(200, 350)

        # Behaviour multipliers
        self.aggression = random.uniform(1.3, 2.2)
        self.drift_factor = random.uniform(0.8, 1.6)

    def update(self):
        """Simulates movement per tick"""

        # Aggressive acceleration/braking randomly
        if random.random() < 0.65:
            self.speed += random.uniform(1.5, 4.5) * self.aggression
        else:
            self.speed -= random.uniform(1.0, 3.5)

        # Clamp speed
        self.speed = max(10, min(self.speed, 60))

        # Random steering changes (aggressive correction)
        self.heading += random.uniform(-8, 8) * self.drift_factor

        # Normalize heading
        if self.heading < 0:
            self.heading += 360
        elif self.heading >= 360:
            self.heading -= 360

        # Update position using heading angle
        rad = self.heading * (3.14159 / 180)

        self.x += self.speed * 0.1 * (random.uniform(0.9, 1.1)) * (1 if random.random() > 0.1 else -1) * (0.5 + random.random())
        self.y += self.speed * 0.1 * random.uniform(-1.2, 1.2)

    def get_state(self) -> Dict:
        """Return full state for API response"""

        return {
            "id": self.id,
            "x": float(self.x),
            "y": float(self.y),
            "speed": float(self.speed),
            "heading": float(self.heading),
            "color": self.color,
            "type": "aggressive"
        }
