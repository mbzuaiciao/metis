"""Offline checks only; never call the provider or replay an experiment."""
from copy import deepcopy
import importlib.util
import json
import hashlib
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("historical_macro_context", HERE / "historical_macro_context.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def test_frozen_pair_and_no_event_leakage():
    prepared = study.prepare()
    frozen = json.loads(study.PUBLIC.read_text())
    # The completed experiment fingerprints its then-current production sources.
    # Verify that provenance in Git, rather than freezing future product code.
    comparable = deepcopy(prepared)
    for source in ('backend/metis/reasoning/harness.py', 'backend/metis/analytics/engine.py'):
        historical = subprocess.check_output(['git', 'show', f'2b75a7c:{source}'], cwd=HERE.parent)
        assert hashlib.sha256(historical).hexdigest() == frozen['source_sha256'][source]
        comparable['source_sha256'][source] = frozen['source_sha256'][source]
    assert comparable == frozen
    a, b = prepared["contexts"]["A"], deepcopy(prepared["contexts"]["B"])
    macro = b.pop("macro_context")
    assert a == b
    assert macro["sources"]["bls"]["published_at"] == "2022-09-13T08:30:00-04:00"
    plain = json.dumps(a).lower()
    for clue in ("2022", "2025", "september", "cpi", "inflation surprise", "bls.gov", "marketscreener.com"):
        assert clue not in plain
    assert study.digest(a["financial_inputs"]) == prepared["financial_sha256"]


def test_source_units_omissions_and_hypothetical_pnl():
    prepared = study.prepare()
    financial = prepared["contexts"]["A"]["financial_inputs"]
    result = financial["calculated_partial_factor_pnl"]
    assert result["shocks"] == {"rates_bp": 5.37, "ig_bp": 0, "hy_bp": 0, "equity_pct": -4.32, "fx_pct": -1.46}
    assert result["by_factor"] == {"rates_pnl": -276877.2, "credit_pnl": 0, "equity_pnl": -993600, "fx_pnl": -146000}
    assert result["total_pnl_usd"] == pytest.approx(-1416477.2)
    positions = {p["id"]: p for p in result["positions"]}
    assert positions["IRS-P"]["rates_pnl"] == 64440
    assert positions["IRS-R"]["rates_pnl"] == -150360
    for bucket in ("ig_spread", "hy_spread"):
        assert financial["observations"][bucket]["change_bp"] is None
    assert "unknown" in financial["coverage"]["credit_spreads"]
    assert "partial-factor" in financial["coverage"]["total"]
    inputs = json.loads(study.INPUT.read_text())
    for observation in inputs["observations"].values():
        assert inputs["sources"][observation["source"]]["url"].startswith("https://")
    two = inputs["observations"]["ust2"]
    assert (two["current_yield_pct"] - two["previous_yield_pct"]) * 100 == pytest.approx(17.24)


def test_original_daily_and_scenarios_unchanged():
    from metis.analytics.engine import Shocks, calculate, load_json, load_positions, workstation
    before = workstation()
    study.prepare()
    assert workstation() == before
    assert before["market"]["as_of"] == "2025-03-10"
    assert before["daily"]["total_pnl_usd"] == -560770
    preset = next(s for s in load_json("scenarios") if s["id"] == "risk-off")
    assert calculate(load_positions(), Shocks(**preset["shocks"]))["total_pnl_usd"] == -3347000
