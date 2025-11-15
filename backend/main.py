import asyncio
from typing import Dict, Any, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.simulation_engine import SimulationEngine
from backend.monte_carlo import MonteCarloSimulator

app = FastAPI()

# Allow frontend + electron
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==== GLOBAL STATE =====
engine: Optional[SimulationEngine] = None
_simulation_task: Optional[asyncio.Task] = None
_latest_state: Optional[Dict[str, Any]] = None

# === TRACK + DEFAULT AGENTS ===
TRACK_POINTS = [
    {"x": 100, "y": 100},
    {"x": 400, "y": 80},
    {"x": 500, "y": 150},
    {"x": 520, "y": 300},
    {"x": 400, "y": 400},
    {"x": 100, "y": 420},
    {"x": 50, "y": 250},
]

DEFAULT_AGENTS = [
    {"id": "CAR_1", "color": "#00FFD1", "personality": "aggressive", "controller": "aggressive"},
    {"id": "CAR_2", "color": "#FF4D4D", "personality": "neutral", "controller": "rule_based"},
    {"id": "CAR_3", "color": "#FFD700", "personality": "cautious", "controller": "rule_based"},
]

# ==== REQUEST MODELS ====
class StartSimulationRequest(BaseModel):
    agents: Optional[List[Dict[str, Any]]] = None
    max_laps: int = 5
    tick_dt: float = 0.1


class MonteCarloRequest(BaseModel):
    target_agent_id: str
    runs: int = 100
    max_laps: int = 5
    tick_dt: float = 0.1
    agents: Optional[List[Dict[str, Any]]] = None


# ==== API ROUTES ====

@app.post("/simulation/start")
async def start_simulation(req: StartSimulationRequest):
    global engine, _simulation_task, _latest_state

    configs = req.agents or DEFAULT_AGENTS
    engine = SimulationEngine(
        track_points=TRACK_POINTS,
        agent_configs=configs,
        tick_dt=req.tick_dt,
        max_laps=req.max_laps,
    )

    # Reset first frame
    _latest_state = engine.reset().to_dict()

    # Stop an old loop if running
    if _simulation_task is not None:
        _simulation_task.cancel()

    async def simulation_loop():
        global _latest_state
        try:
            while True:
                await asyncio.sleep(req.tick_dt)
                if engine is None:
                    break
                state = engine.step()
                _latest_state = state.to_dict()
        except asyncio.CancelledError:
            pass

    _simulation_task = asyncio.create_task(simulation_loop())

    return {"status": "started", "agents": [a["id"] for a in configs]}


@app.get("/simulation/state")
async def simulation_state():
    if _latest_state is None:
        return {"status": "no_simulation"}
    return _latest_state


@app.post("/montecarlo/run")
async def run_monte_carlo(req: MonteCarloRequest):
    configs = req.agents or DEFAULT_AGENTS

    simulator = MonteCarloSimulator(
        base_track_points=TRACK_POINTS,
        base_agent_configs=configs,
        max_laps=req.max_laps,
        tick_dt=req.tick_dt,
    )

    result = simulator.run(target_agent_id=req.target_agent_id, runs=req.runs)

    return {
        "agent_name": result.agent_name,
        "win_prob": result.win_prob,
        "margin": result.margin,
        "ci_low": result.ci_low,
        "ci_high": result.ci_high,
        "mean_finish_time": result.mean_finish_time,
        "ci_time_low": result.ci_time_low,
        "ci_time_high": result.ci_time_high,
        "formatted": result.formatted(),
    }


# Allow local run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
