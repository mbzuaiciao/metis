"""USD linear exposures. Positive DV01/CS01 = gain when yields/spreads FALL 1bp."""
import json
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

PortfolioId = Literal["current", "candidate-a", "candidate-b", "candidate-c"]

DATA = Path(__file__).resolve().parents[1] / "data"


class Shocks(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    rates_bp: float = Field(default=0, ge=-300, le=300)
    ig_bp: float = Field(default=0, ge=-300, le=500)
    hy_bp: float = Field(default=0, ge=-500, le=1500)
    equity_pct: float = Field(default=0, ge=-60, le=60)
    fx_pct: float = Field(default=0, ge=-30, le=30)


def load_json(name: str):
    return json.loads((DATA / f"{name}.json").read_text())


def snapshot_files(investigation_date: str | None = None) -> dict:
    config = load_json('investigation')
    investigation_date = config['default_date'] if investigation_date is None else investigation_date
    snapshots = config['snapshots']
    if investigation_date not in snapshots:
        raise ValueError(f'Investigation data unavailable for {investigation_date}; no data was substituted.')
    return snapshots[investigation_date]


def load_positions(investigation_date: str | None = None, portfolio_id: PortfolioId = "current") -> pd.DataFrame:
    if portfolio_id not in {"current", "candidate-a", "candidate-b", "candidate-c"}:
        raise ValueError("Unknown portfolio selection")
    if portfolio_id != "current" and investigation_date not in {None, "2026-10-30"}:
        raise ValueError("Candidate portfolios are available only as of 2026-10-30; no data was substituted.")
    filename = snapshot_files(investigation_date)['positions']
    frame = pd.read_csv(DATA / filename, keep_default_na=False)
    numeric = ["market_value_usd", "notional_usd", "dv01_usd_per_bp", "cs01_usd_per_bp", "equity_delta_usd", "fx_delta_usd"]
    if frame.empty or frame.id.duplicated().any() or not np.isfinite(frame[numeric].to_numpy(dtype=float)).all():
        raise ValueError("Invalid portfolio data")
    if not set(frame.spread_bucket).issubset({"ig", "hy", "none"}):
        raise ValueError("Unknown spread bucket")
    if portfolio_id == "candidate-a":
        # Illustrative construction, not an optimized allocation. Keep the original fixtures immutable.
        hy = frame.id.isin(["HY-US", "HY-EU"])
        proceeds = float(frame.loc[hy, "market_value_usd"].sum()) * 0.25
        frame.loc[hy, numeric] *= 0.75
        frame.loc[frame.id == "CASH", ["market_value_usd", "notional_usd"]] += proceeds
    elif portfolio_id == "candidate-b":
        # Reallocate $9m within the government cash-bond sleeve; leave swaps unchanged.
        fields = ["market_value_usd", "notional_usd", "dv01_usd_per_bp"]
        frame.loc[frame.id == "UST10", fields] *= 0.5
        frame.loc[frame.id == "UST2", fields] *= 1.9
    elif portfolio_id == "candidate-c":
        equity = frame.id.isin(["EQ-US", "EQ-DM"])
        proceeds = float(frame.loc[equity, "market_value_usd"].sum()) * 0.5
        frame.loc[equity, ["market_value_usd", "notional_usd", "equity_delta_usd"]] *= 0.5
        frame.loc[frame.id == "CASH", ["market_value_usd", "notional_usd"]] += proceeds
    return frame


def exposures(frame: pd.DataFrame) -> dict:
    return {
        "dv01_usd_per_bp": float(frame.dv01_usd_per_bp.sum()),
        "cs01_usd_per_bp": float(frame.cs01_usd_per_bp.sum()),
        "ig_cs01_usd_per_bp": float(frame.loc[frame.spread_bucket == "ig", "cs01_usd_per_bp"].sum()),
        "hy_cs01_usd_per_bp": float(frame.loc[frame.spread_bucket == "hy", "cs01_usd_per_bp"].sum()),
        "equity_delta_usd": float(frame.equity_delta_usd.sum()),
        "fx_delta_usd": float(frame.fx_delta_usd.sum()),
    }


def calculate(frame: pd.DataFrame, shocks: Shocks) -> dict:
    result = frame.copy()
    result["rates_pnl"] = -result.dv01_usd_per_bp * shocks.rates_bp
    spread = np.select([result.spread_bucket == "ig", result.spread_bucket == "hy"], [shocks.ig_bp, shocks.hy_bp], default=0)
    result["credit_pnl"] = -result.cs01_usd_per_bp * spread
    result["equity_pnl"] = result.equity_delta_usd * shocks.equity_pct / 100
    result["fx_pnl"] = result.fx_delta_usd * shocks.fx_pct / 100
    factors = ["rates_pnl", "credit_pnl", "equity_pnl", "fx_pnl"]
    result[factors] = result[factors].round(2)
    result["pnl_usd"] = result[factors].sum(axis=1).round(2)
    total = float(result.pnl_usd.sum())
    nav = float(frame.market_value_usd.sum())
    return {"shocks": shocks.model_dump(), "total_pnl_usd": total, "pnl_pct_nav": total / nav * 100,
            "by_factor": {key: float(result[key].sum()) for key in factors},
            "by_asset_class": result.groupby("asset_class", sort=False).pnl_usd.sum().reset_index().to_dict(orient="records"),
            "positions": result.to_dict(orient="records"), "method": "First-order linear approximation; no carry, convexity, defaults, liquidity or funding costs."}


def workstation(investigation_date: str | None = None, portfolio_id: PortfolioId = "current") -> dict:
    frame = load_positions(investigation_date, portfolio_id)
    market = load_json(snapshot_files(investigation_date)['market'])
    daily = calculate(frame, Shocks(**market["daily_shocks"]))
    nav = float(frame.market_value_usd.sum())
    # End-of-day NAV consists of the displayed marks. Daily P&L reconciles to opening NAV.
    opening = nav - daily["total_pnl_usd"]
    allocation = frame.groupby("asset_class", sort=False).market_value_usd.sum().reset_index().to_dict(orient="records")
    return {"portfolio_name": "Metis Global Opportunities" if portfolio_id == "current" else {
                "candidate-a": "Candidate A — Reduced HY Exposure",
                "candidate-b": "Candidate B — Shorter Duration",
                "candidate-c": "Candidate C — Defensive Equity",
            }[portfolio_id], "data_kind": "synthetic", "nav_usd": nav,
            "opening_nav_usd": opening, "daily_return_pct": daily["total_pnl_usd"] / opening * 100,
            "positions": daily["positions"], "allocation": allocation, "exposures": exposures(frame),
            "daily": daily, "market": market, "scenarios": load_json("scenarios"), "historical_stress_presets": load_json("historical-stress-presets"), "history": load_json("history")}


def portfolio_selections() -> list[dict]:
    return [
        {"id": "current", "label": "Current Portfolio", "reference_date": "2026-10-30",
         "construction": "Existing illustrative October 30, 2026 holdings.", "snapshot": workstation("2026-10-30")},
        {"id": "candidate-a", "label": "Candidate A — Reduced HY Exposure", "reference_date": "2026-10-30",
         "construction": "Illustrative, not optimal: reduce each US/EU HY basket by 25% ($2m/$1.5m); transfer $3.5m to USD cash. Scale HY notionals, DV01 and CS01 proportionately. NAV stays $100m; no transaction costs or execution assumptions.",
         "snapshot": workstation("2026-10-30", "candidate-a")},
        {"id": "candidate-b", "label": "Candidate B — Shorter Duration", "reference_date": "2026-10-30",
         "construction": "Illustrative, first-order, not optimized: move $9m from UST10 ($18m to $9m) into UST2 ($10m to $19m), scaling each bond's notional and DV01 proportionately. Shorter government bond sleeve only; swaps and cash unchanged. NAV stays $100m. Constructed independently from Current, not historical realized returns or a trade recommendation.",
         "snapshot": workstation("2026-10-30", "candidate-b")},
        {"id": "candidate-c", "label": "Candidate C — Defensive Equity", "reference_date": "2026-10-30",
         "construction": "Illustrative, first-order, not optimized: halve US/ex-US equity market values, notionals and deltas to $8.5m/$4.5m; transfer $13m to USD cash ($4m to $17m). All other exposures unchanged; NAV stays $100m. Constructed independently from Current, not a hedge, historical realized returns or a trade recommendation.",
         "snapshot": workstation("2026-10-30", "candidate-c")},
    ]
