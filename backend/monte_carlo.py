from typing import List, Dict, Any
import numpy as np

from backend.models import AgentState, SimulationState
from .models import MonteCarloResult


class MonteCarloSimulator:
    def __init__(
        self,
        base_track_points: List[Dict[str, float]],
        base_agent_configs: List[Dict[str, Any]],
        max_laps: int = 5,
        tick_dt: float = 0.1,
    ):
        self.track_points = base_track_points
        self.agent_configs = base_agent_configs
        self.max_laps = max_laps
        self.tick_dt = tick_dt

    def _run_single_race(self) -> Dict[str, float]:
        engine = SimulationEngine(
            self.track_points, self.agent_configs, self.tick_dt, self.max_laps
        )
        finish_times: Dict[str, float] = {cfg["id"]: None for cfg in self.agent_configs}

        # Run until all finished or timeout
        max_time = 2000.0
        while engine.time < max_time:
            state = engine.step()
            all_done = True
            for agent in state.agents:
                if finish_times[agent.id] is None and agent.status == "FINISHED":
                    finish_times[agent.id] = state.time
                if finish_times[agent.id] is None and agent.status in ("RACING",):
                    all_done = False
            if all_done:
                break

        # Assign big penalty time for DNF / unfinished
        for aid, t in finish_times.items():
            if t is None:
                finish_times[aid] = max_time

        return finish_times

    def run(self, target_agent_id: str, runs: int = 100) -> MonteCarloResult:
        finish_times_per_run: List[Dict[str, float]] = []

        for i in range(runs):
            ft = self._run_single_race()
            finish_times_per_run.append(ft)

        # Win probability – xi = 1 if agent has min finish time in a run, else 0
        win_indicators: List[int] = []
        target_times: List[float] = []

        for ft in finish_times_per_run:
            # Determine winner
            winner_id = min(ft, key=lambda k: ft[k])
            win_indicators.append(1 if winner_id == target_agent_id else 0)
            target_times.append(ft[target_agent_id])

        x = np.array(win_indicators, dtype=float)
        t = np.array(target_times, dtype=float)
        N = len(x)

        # Monte Carlo mean and variance
        mu_win = x.mean()
        var_win = ((x - mu_win) ** 2).mean()
        sigma_win = np.sqrt(var_win)

        # 95% CI margin for probability
        se_win = sigma_win / np.sqrt(N)
        margin = 1.96 * se_win
        ci_low = max(0.0, mu_win - margin)
        ci_high = min(1.0, mu_win + margin)

        # Finish time stats
        mu_time = t.mean()
        var_time = ((t - mu_time) ** 2).mean()
        sigma_time = np.sqrt(var_time)
        se_time = sigma_time / np.sqrt(N)
        margin_time = 1.96 * se_time
        ci_time_low = mu_time - margin_time
        ci_time_high = mu_time + margin_time

        result = MonteCarloResult(
            agent_name=target_agent_id,
            win_prob=mu_win,
            margin=margin,
            ci_low=ci_low,
            ci_high=ci_high,
            mean_finish_time=mu_time,
            ci_time_low=ci_time_low,
            ci_time_high=ci_time_high,
        )

        print(result.formatted())
        return result
