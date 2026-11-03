"""USD linear exposures. Positive DV01/CS01 = gain when yields/spreads FALL 1bp."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

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


def load_positions(investigation_date: str | None = None) -> pd.DataFrame:
    filename = snapshot_files(investigation_date)['positions']
    frame = pd.read_csv(DATA / filename, keep_default_na=False)
    numeric = ["market_value_usd", "notional_usd", "dv01_usd_per_bp", "cs01_usd_per_bp", "equity_delta_usd", "fx_delta_usd"]
    if frame.empty or frame.id.duplicated().any() or not np.isfinite(frame[numeric].to_numpy(dtype=float)).all():
        raise ValueError("Invalid portfolio data")
    if not set(frame.spread_bucket).issubset({"ig", "hy", "none"}):
        raise ValueError("Unknown spread bucket")
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


def workstation(investigation_date: str | None = None) -> dict:
    frame = load_positions(investigation_date)
    market = load_json(snapshot_files(investigation_date)['market'])
    daily = calculate(frame, Shocks(**market["daily_shocks"]))
    nav = float(frame.market_value_usd.sum())
    # End-of-day NAV consists of the displayed marks. Daily P&L reconciles to opening NAV.
    opening = nav - daily["total_pnl_usd"]
    allocation = frame.groupby("asset_class", sort=False).market_value_usd.sum().reset_index().to_dict(orient="records")
    return {"portfolio_name": "Metis Global Opportunities", "data_kind": "synthetic", "nav_usd": nav,
            "opening_nav_usd": opening, "daily_return_pct": daily["total_pnl_usd"] / opening * 100,
            "positions": daily["positions"], "allocation": allocation, "exposures": exposures(frame),
            "daily": daily, "market": market, "scenarios": load_json("scenarios"), "historical_stress_presets": load_json("historical-stress-presets"), "history": load_json("history")}
