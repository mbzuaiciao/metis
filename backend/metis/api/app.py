from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from metis.analytics.engine import Shocks, calculate, load_positions, workstation
from metis.reasoning.harness import ProviderError, ReasoningRequest, reason

load_dotenv()
app = FastAPI(title="Metis", version="0.1.0")


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/workstation")
def get_workstation():
    return workstation()


@app.post("/api/scenario")
def scenario(shocks: Shocks):
    return calculate(load_positions(), shocks)


@app.post("/api/reasoning")
def reasoning(request: ReasoningRequest):
    try:
        return reason(request)
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
