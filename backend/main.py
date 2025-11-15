import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from typing import Dict, Any, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from simulation.simulation_engine import SimulationEngine
from simulation.controllers.driver_style_controller import DriverStyleController
from montecarlo.montecarlo import MonteCarloSimulator




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


# ==== LOAD DRIVER AI PROFILES ==== #
with open("backend/driver_profiles/driver_profiles.json", "r") as f:
    DRIVER_PROFILES = json.load(f)


# ==== GLOBAL STATE =====
engine: Optional[SimulationEngine] = None
_simulation_task: Optional[asyncio.Task] = None
_latest_state: Optional[Dict[str, Any]] = None


# === TRACK (temporary until we use PNG racing) ===
TRACK_POINTS = [
    {"x": 100, "y": 100},
    {"x": 400, "y": 80},
    {"x": 500, "y": 150},
    {"x": 520, "y": 300},
    {"x": 400, "y": 400},
    {"x": 100, "y": 420},
    {"x": 50, "y": 250},
]


# === BEFORE: Fake personalities
# === NOW: Real driver codes (matches profiles.json)
DEFAULT_AGENTS = [
    {"id": "VER", "color": "#00FFD1"},
    {"id": "HAM", "color": "#FF4D4D"},
    {"id": "LEC", "color": "#FFD700"},
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

    # Inject REAL controllers
    for agent in configs:
        driver_id = agent["id"]
        controller = DriverStyleController(driver_id, DRIVER_PROFILES[driver_id])
        agent["controller"] = controller  # override fake values

    engine = SimulationEngine(
        track_points=TRACK_POINTS,
        agent_configs=configs,
        tick_dt=req.tick_dt,
        max_laps=req.max_laps,
    )

    _latest_state = engine.reset().to_dict()

    if _simulation_task:
        _simulation_task.cancel()

    async def simulation_loop():
        global _latest_state
        try:
            while True:
                await asyncio.sleep(req.tick_dt)
                if engine is None:
                    break
                _latest_state = engine.step().to_dict()
        except asyncio.CancelledError:
            pass

    _simulation_task = asyncio.create_task(simulation_loop())

    return {"status": "started", "agents": [a["id"] for a in configs]}


@app.get("/simulation/state")
async def simulation_state():
    return _latest_state or {"status": "no_simulation"}


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

    return result.formatted()


# Local run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
