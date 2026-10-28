import pytest
from metis.analytics.engine import Shocks, calculate, exposures, load_json, load_positions, workstation


def test_load_and_accounting():
    data = workstation()
    assert len(data["positions"]) == 12
    assert data["nav_usd"] == 100_000_000
    assert sum(x["market_value_usd"] for x in data["allocation"]) == data["nav_usd"]
    assert data["opening_nav_usd"] + data["daily"]["total_pnl_usd"] == data["nav_usd"]


def test_aggregate_exposures():
    e = exposures(load_positions())
    assert e["dv01_usd_per_bp"] == 51_560
    assert e["cs01_usd_per_bp"] == 15_950
    assert e["ig_cs01_usd_per_bp"] == 11_500
    assert e["hy_cs01_usd_per_bp"] == 4_450
    assert e["equity_delta_usd"] == 23_000_000
    assert e["fx_delta_usd"] == 10_000_000


def test_daily_attribution():
    d = workstation()["daily"]
    assert d["by_factor"] == {"rates_pnl": 412_480, "credit_pnl": -407_250, "equity_pnl": -506_000, "fx_pnl": -60_000}
    assert d["total_pnl_usd"] == -560_770
    assert sum(p["pnl_usd"] for p in d["positions"]) == d["total_pnl_usd"]
    assert sum(d["by_factor"].values()) == d["total_pnl_usd"]
    assert sum(a["pnl_usd"] for a in d["by_asset_class"]) == d["total_pnl_usd"]


def test_signs_and_units():
    frame = load_positions()
    d = calculate(frame, Shocks(rates_bp=1, ig_bp=1, hy_bp=1, equity_pct=1, fx_pct=1))
    assert d["by_factor"] == {"rates_pnl": -51_560, "credit_pnl": -15_950, "equity_pnl": 230_000, "fx_pnl": 100_000}
    payer = next(p for p in d["positions"] if p["id"] == "IRS-P")
    assert payer["rates_pnl"] == 12_000
    assert calculate(frame, Shocks())["total_pnl_usd"] == 0


@pytest.mark.parametrize("scenario_id,expected", [("rally", 2_578_000), ("selloff", -2_578_000), ("credit", -1_242_500), ("risk-off", -3_347_000)])
def test_predefined_scenarios(scenario_id, expected):
    s = next(s for s in load_json("scenarios") if s["id"] == scenario_id)
    assert calculate(load_positions(), Shocks(**s["shocks"]))["total_pnl_usd"] == expected


def test_linear_superposition():
    frame = load_positions()
    a = calculate(frame, Shocks(rates_bp=-25))["total_pnl_usd"]
    b = calculate(frame, Shocks(hy_bp=100, equity_pct=-10))["total_pnl_usd"]
    assert calculate(frame, Shocks(rates_bp=-25, hy_bp=100, equity_pct=-10))["total_pnl_usd"] == a + b
