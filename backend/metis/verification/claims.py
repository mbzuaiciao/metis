"""Verify explicit mappings against application-owned calculation snapshots only."""
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FinancialClaim(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, strict=True)
    statement: str = Field(min_length=1, max_length=1500)
    # Strict provider schema uses bounded labels. Unknown labels submitted through
    # other paths remain strings and get Not checked; they are never coerced.
    kind: str = Field(min_length=1, max_length=80, json_schema_extra={"enum": ["number", "sign", "hedge_vs_total", "unmeasured_risk", "dv01_decomposition", "other"]})
    period: str = Field(min_length=1, max_length=80)
    target: str = Field(min_length=1, max_length=160)
    metric: str = Field(min_length=1, max_length=80)
    assertion: str = Field(min_length=1, max_length=80)
    value: float | None = Field(ge=-1e15, le=1e15)
    rounding: str = Field(min_length=1, max_length=80)
    components: list[str] = Field(max_length=12)


def claim(statement, kind, metric, assertion, value=None, *, period="daily", target="portfolio", rounding="exact", components=None):
    return FinancialClaim(statement=statement, kind=kind, period=period, target=target,
                          metric=metric, assertion=assertion, value=value, rounding=rounding, components=components or [])


PNL = {"total_pnl_usd", "pnl_usd", "rates_pnl", "credit_pnl", "equity_pnl", "fx_pnl"}
SENSITIVITIES = {"dv01_usd_per_bp", "cs01_usd_per_bp", "ig_cs01_usd_per_bp", "hy_cs01_usd_per_bp"}
MISSING = {
    "funding": "Unencumbered cash, funding facilities, timing and contractual terms",
    "margin": "CSA/netting terms, collateral balances/eligibility and margin requirements",
    "liquidity": "Executable prices, bid-ask spreads, market depth and liquidation horizons",
    "default": "Issuer concentrations, default scenarios, recovery and migration assumptions",
}
COVERAGE = "Only the explicit structured assertion is checked. Original wording, causal explanations and omitted claims are Not checked."


def rows_for(target, positions):
    if target == "portfolio":
        return positions
    prefix, _, key = target.partition(":")
    field = {"position": "id", "asset_class": "asset_class", "spread_bucket": "spread_bucket"}.get(prefix)
    return [p for p in positions if p[field] == key] if field else []


def verify_claim(c: FinancialClaim, context: dict) -> dict:
    evidence = []
    period = {"daily": "Daily snapshot", "scenario": "Selected scenario"}.get(c.period, c.period)
    target = c.target.replace("position:", "Position ").replace("asset_class:", "Asset class ").replace("spread_bucket:", "Credit bucket ")
    labels = {"total_pnl_usd": "total P&L", "pnl_usd": "net P&L", "rates_pnl": "government-rate P&L", "credit_pnl": "spread-only P&L", "equity_pnl": "equity P&L", "fx_pnl": "FX P&L", "dv01_usd_per_bp": "DV01", "cs01_usd_per_bp": "CS01", "ig_cs01_usd_per_bp": "IG CS01", "hy_cs01_usd_per_bp": "HY CS01", "loss_usd": "loss"}
    mapping = f"{period} · {target} · {labels.get(c.metric, c.metric)}"
    if c.kind == "hedge_vs_total":
        rules_text = {"rates_loss_total_loss_yields_down": "Yields declined; rates lost money and the portfolio lost money.", "rates_gain_total_loss_yields_down": "Yields declined; rates gained while the portfolio lost money.", "rates_gain_total_gain_yields_down": "Yields declined; rates gained and the portfolio made money."}
        mapping = f"{period}: " + rules_text.get(c.assertion, c.assertion)
    elif c.kind == "unmeasured_risk":
        text = {"not_quantified": "is not quantified by this model", "loss_exists": "is asserted to exist", "loss_absent": "is asserted to be absent", "buffer_adequate": "buffer is asserted adequate", "buffer_inadequate": "buffer is asserted inadequate", "loss_equals": "is asserted equal to"}
        mapping += " " + text.get(c.assertion, c.assertion)
    else:
        mapping += " " + {"equals": "equals", "positive": "is positive", "negative": "is negative", "zero": "is zero"}.get(c.assertion, c.assertion)
    if c.value is not None:
        unit = "USD/bp" if c.metric in SENSITIVITIES else "USD"
        mapping += f" {c.value:,.2f} {unit} (precision: {c.rounding})"
    if c.components:
        mapping += " · exhaustive components: " + ", ".join(c.components)

    def finish(verdict, explanation, limitation=""):
        return {"claim": c.model_dump(), "mapping": mapping, "verdict": verdict,
                "explanation": explanation, "evidence": evidence,
                "limitations": [COVERAGE] + ([limitation] if limitation else []),
                "original_wording_status": "Not checked"}

    def fact(path, value):
        evidence.append({"path": path, "value": value})

    if c.kind not in {"number", "sign", "hedge_vs_total", "unmeasured_risk", "dv01_decomposition"}:
        return finish("Not checked", "Claim type is outside the supported verification scope.")
    if c.period not in {"daily", "scenario"} or c.period not in context:
        return finish("Not checked", "No supported calculation period was mapped.")
    calc = context[c.period]
    positions = calc["positions"]
    if c.kind != "dv01_decomposition" and c.components:
        return finish("Not checked", "Unexpected components: the mapping is not supported.")

    if c.kind == "unmeasured_risk":
        if c.target not in MISSING or c.metric != "loss_usd" or c.rounding != "exact":
            return finish("Not checked", "Unsupported risk/metric mapping.")
        if c.assertion not in {"not_quantified", "loss_equals", "loss_exists", "loss_absent", "buffer_adequate", "buffer_inadequate"}:
            return finish("Not checked", "Unsupported unmeasured-risk assertion.")
        if c.assertion != "loss_equals" and c.value is not None:
            return finish("Not checked", "Unexpected numeric value for this assertion.")
        fact(f"{c.period}.method", calc["method"])
        fact("missing_inputs", MISSING[c.target])
        if c.target in {"funding", "margin"}:
            for p in positions:
                if p["id"] == "CASH":
                    fact(f"{c.period}.positions[CASH].market_value_usd", p["market_value_usd"])
        if c.assertion == "not_quantified":
            return finish("Verified", "This linear model does not quantify this loss channel.", "This does not mean the loss is zero or that no partial information exists.")
        return finish("Not established", "The available model and inputs cannot determine this loss or buffer adequacy.", MISSING[c.target] + " are needed; absence from modeled P&L is not proof of zero risk.")

    if c.kind == "hedge_vs_total":
        if c.target != "portfolio" or c.metric != "rates_pnl" or c.value is not None or c.rounding != "exact":
            return finish("Not checked", "Unsupported hedge-versus-total mapping.")
        rules = {"rates_loss_total_loss_yields_down": (-1, -1), "rates_gain_total_loss_yields_down": (1, -1), "rates_gain_total_gain_yields_down": (1, 1)}
        if c.assertion not in rules:
            return finish("Not checked", "Unsupported hedge-versus-total assertion.")
        rates, total, move = calc["by_factor"]["rates_pnl"], calc["total_pnl_usd"], calc["shocks"]["rates_bp"]
        for path, value in [("shocks.rates_bp", move), ("by_factor.rates_pnl", rates), ("total_pnl_usd", total)]:
            fact(f"{c.period}.{path}", value)
        for key in ["credit_pnl", "equity_pnl", "fx_pnl"]:
            fact(f"{c.period}.by_factor.{key}", calc["by_factor"][key])
        # Treasury cash holdings are a subset of the government-rate factor.
        treasury = [p for p in positions if p["id"] in {"UST10", "UST2"}]
        for p in treasury:
            fact(f"{c.period}.positions[{p['id']}].rates_pnl", p["rates_pnl"])
        expected_rate, expected_total = rules[c.assertion]
        matches = move < 0 and rates * expected_rate > 0 and total * expected_total > 0
        return finish("Verified" if matches else "Contradicted",
                      "Yield direction, rates contribution and total P&L " + ("match" if matches else "do not match") + " the mapped premises.",
                      "Rates P&L includes swaps and credit-bond rate legs, not only Treasuries. This checks premises, not causal attribution.")

    if c.kind == "dv01_decomposition":
        if c.target != "portfolio" or c.metric != "dv01_usd_per_bp" or c.assertion != "equals" or c.value is None or c.rounding != "exact" or not c.components:
            return finish("Not checked", "A decomposition requires portfolio DV01, equals, an exact value and explicit components.")
        seen = set()
        total = Decimal(0)
        for component in c.components:
            rows = rows_for(component, positions)
            if not rows:
                return finish("Not checked", "An unknown component cannot be checked.")
            ids = {p["id"] for p in rows}
            fact(component + ".member_ids", ", ".join(sorted(ids)))
            if seen & ids:
                fact("overlapping_position_ids", ", ".join(sorted(seen & ids)))
                return finish("Contradicted", "The proposed additive decomposition counts positions more than once.")
            seen |= ids
            contribution = sum(Decimal(str(p["dv01_usd_per_bp"])) for p in rows)
            total += contribution
            fact(component + ".dv01_usd_per_bp", float(contribution))
        required = {p["id"] for p in positions if p["dv01_usd_per_bp"] != 0}
        actual = context["portfolio"]["exposures"]["dv01_usd_per_bp"]
        fact("portfolio.exposures.dv01_usd_per_bp", actual)
        matches = required <= seen and total == Decimal(str(actual)) and abs(Decimal(str(c.value)) - total) <= Decimal("0.01")
        return finish("Verified" if matches else "Contradicted", "An exhaustive, disjoint DV01 decomposition is required; component totals and claimed total must agree with portfolio DV01.")

    if c.metric not in PNL | SENSITIVITIES:
        return finish("Not checked", "Metric is outside the supported P&L/sensitivity scope.")
    rows = rows_for(c.target, positions)
    if not rows:
        return finish("Not checked", "Unknown position or group; no calculation was matched.")
    if c.target == "portfolio" and c.metric in context["portfolio"]["exposures"]:
        actual = context["portfolio"]["exposures"][c.metric]
        fact("portfolio.exposures." + c.metric, actual)
    elif c.target == "portfolio" and c.metric == "total_pnl_usd":
        actual = calc["total_pnl_usd"]
        fact(c.period + ".total_pnl_usd", actual)
    elif c.target == "portfolio" and c.metric in calc["by_factor"]:
        actual = calc["by_factor"][c.metric]
        fact(c.period + ".by_factor." + c.metric, actual)
    else:
        key = "pnl_usd" if c.metric == "total_pnl_usd" else c.metric
        if any(key not in p for p in rows):
            return finish("Not checked", "This metric is unavailable at the mapped target.")
        actual = float(sum(Decimal(str(p[key])) for p in rows))
        for p in rows:
            fact(f"{c.period}.positions[{p['id']}].{key}", p[key])
        fact("mapped_target_total." + c.metric, actual)
    if c.kind == "sign":
        if c.value is not None or c.rounding != "exact" or c.assertion not in {"positive", "negative", "zero"}:
            return finish("Not checked", "Unsupported sign mapping.")
        matches = {"positive": actual > 0, "negative": actual < 0, "zero": actual == 0}[c.assertion]
        return finish("Verified" if matches else "Contradicted", "The mapped sign is compared directly with the backend value; positive DV01/CS01 gains on a 1bp decline.")
    if c.assertion != "equals" or c.value is None:
        return finish("Not checked", "A numerical claim requires an equals assertion and finite value.")
    tolerances = {"exact": Decimal("0.01"), "whole": Decimal("0.5"), "million_2dp": Decimal("5000")}
    if c.rounding not in tolerances or (c.rounding == "million_2dp" and c.metric in SENSITIVITIES):
        return finish("Not checked", "Unsupported rounding precision for this metric.")
    value = Decimal(str(c.value))
    quantum = {"whole": Decimal(1), "million_2dp": Decimal(10000)}.get(c.rounding)
    if quantum and value % quantum != 0:
        return finish("Not checked", "Claimed value does not use its declared rounding precision.")
    tolerance = tolerances[c.rounding]
    fact("absolute_tolerance", float(tolerance))
    matches = abs(value - Decimal(str(actual))) <= tolerance
    return finish("Verified" if matches else "Contradicted", "The claimed value " + ("matches" if matches else "differs from") + " the backend value at the declared absolute tolerance.", "Tolerance is in USD for P&L or USD/bp for sensitivities. It does not validate wording or economic causation.")


def verify_claims(claims, context):
    return [verify_claim(c, context) for c in claims]


def demonstration_claims():
    return [
        claim("The portfolio lost money because its Treasury hedge generated losses as yields fell.", "hedge_vs_total", "rates_pnl", "rates_loss_total_loss_yields_down"),
        claim("Yields fell and the rate hedge contributed positively, but credit, equity and FX losses left the portfolio with a daily loss.", "hedge_vs_total", "rates_pnl", "rates_gain_total_loss_yields_down"),
        claim("The USD 6m cash balance is insufficient to meet funding needs during stress.", "unmeasured_risk", "loss_usd", "buffer_inadequate", target="funding"),
    ]
