from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class AgentState:
    id: str
    color: str
    x: float
    y: float
    heading: float
    speed: float
    lap: int
    status: str  # "RACING", "PIT", "DNF"

    segment_index: int
    segment_progress: float  # 0..1 within segment


@dataclass
class SimulationState:
    time: float
    agents: List[AgentState]
    event_log: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "time": self.time,
            "agents": [asdict(a) for a in self.agents],
            "event_log": self.event_log,
        }


@dataclass
class MonteCarloResult:
    agent_name: str
    win_prob: float
    margin: float
    ci_low: float
    ci_high: float
    mean_finish_time: float
    ci_time_low: float
    ci_time_high: float

    def formatted(self) -> str:
        return (
            f"Monte Carlo estimated win probability for {self.agent_name}: "
            f"{self.win_prob * 100:.1f}% ± {self.margin * 100:.1f}%\n"
            f"95% CI for average finish time: "
            f"[{self.ci_time_low:.2f}, {self.ci_time_high:.2f}] sec"
        )
