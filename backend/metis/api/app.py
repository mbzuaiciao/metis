import os

from pydantic import BaseModel, ConfigDict, Field
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from metis.analytics.engine import Shocks, calculate, load_positions, workstation
from metis.reasoning.causal import CausalRequest, explore
from metis.reasoning.harness import ProviderError, ReasoningRequest, assemble_context, reason
from metis.verification.claims import FinancialClaim, demonstration_claims, verify_claims

load_dotenv()
app = FastAPI(title="Metis", version="0.1.0")


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/workstation")
def get_workstation():
    return {**workstation(), "causal_mode": os.getenv("METIS_PROVIDER", "demo").strip().lower()}


@app.post("/api/scenario")
def scenario(shocks: Shocks):
    return calculate(load_positions(), shocks)


@app.post("/api/reasoning")
def reasoning(request: ReasoningRequest):
    try:
        return reason(request)
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/causal-exploration")
def causal_exploration(request: CausalRequest):
    try:
        return explore(request)
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


class VerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claims: list[FinancialClaim] = Field(max_length=12)
    shocks: Shocks = Field(default_factory=Shocks)


@app.post("/api/verify-claims")
def verify_financial_claims(request: VerificationRequest):
    # Callers supply assertions and shocks, never truth values or calculations.
    context = assemble_context(request.shocks)
    return {"results": verify_claims(request.claims, context)}


@app.get("/api/verification-demo")
def verification_demo():
    return {"results": verify_claims(demonstration_claims(), assemble_context(Shocks()))}
