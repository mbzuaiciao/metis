import os

from pydantic import BaseModel, ConfigDict, Field
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from metis.analytics.engine import Shocks, calculate, load_json, load_positions, workstation
from metis.reasoning.causal import CausalRequest, explore
from metis.reasoning.followup import EvidenceSnapshots, FollowupRequest, InvestigationRequest, SnapshotUnavailable
from metis.reasoning.harness import ProviderError, assemble_context, reason
from metis.verification.claims import FinancialClaim, demonstration_claims, verify_claims

load_dotenv()
app = FastAPI(title="Metis", version="0.1.0")
evidence_snapshots = EvidenceSnapshots()


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/workstation")
def get_workstation():
    return {**workstation(), "investigation": load_json('investigation'),
            "causal_mode": os.getenv("METIS_PROVIDER", "demo").strip().lower()}


@app.post("/api/scenario")
def scenario(shocks: Shocks):
    return calculate(load_positions(), shocks)


@app.post("/api/reasoning")
def reasoning(request: InvestigationRequest | FollowupRequest):
    try:
        if isinstance(request, FollowupRequest):
            return evidence_snapshots.resume(request)
        if request.investigation_scope == 'daily':
            data = workstation()
            date = request.investigation_date.isoformat() if request.investigation_date else load_json('investigation')['default_date']
            if date != data['market']['as_of']:
                raise HTTPException(status_code=422, detail=(
                    f'Investigation data unavailable for {date}. '
                    f"The available daily snapshot is synthetic and dated {data['market']['as_of']}; "
                    'no data was substituted.'))
            request = request.model_copy(update={'shocks': Shocks(**data['daily']['shocks'])})
        elif request.investigation_date is not None:
            raise HTTPException(status_code=422, detail='investigation_date applies only to daily investigations; historical events and stress scenarios retain their own scope.')
        return evidence_snapshots.capture(reason(request), request.investigation_scope)
    except SnapshotUnavailable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
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
