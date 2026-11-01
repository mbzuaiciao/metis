"""Offline, deliberately constructed routing examples; not an LLM completeness evaluation.

Mirrors only the ordered topic-selection predicates of frontend/src/investigation.ts
at 5f38bc0. No application imports or API calls.
"""
import re

GUIDES = [
    ("Funding & counterparties", r"margin|funding|collateral|counterparty|swap|forward"),
    ("Liquidity", r"liquid|bid.ask|execution|\bsell\b|redemption"),
    ("Joint market moves", r"correlat|divers|equity|equities|inflation|recession"),
    ("Credit", r"credit|default|downgrade|spread|\bHY\b"),
]
CASES = [
    ("Funding pressure as HY spreads widen", {"Funding & counterparties", "Credit"}),
    ("Forced sell-off in equities amid thin market liquidity", {"Liquidity", "Joint market moves"}),
    ("Large debt maturity wall creates refinancing risk", {"Refinancing"}),
    ("Variation margin calls on receive-fixed swaps", {"Funding & counterparties"}),
    ("HY spread widening and issuer default concern", {"Credit"}),
    ("Equities and credit correlations rise in recession", {"Joint market moves", "Credit"}),
]

def route(headline):
    return next((name for name, pattern in GUIDES if re.search(pattern, headline, re.I)), "Model boundaries")

if __name__ == "__main__":
    omitted = 0
    for headline, required in CASES:
        selected = route(headline)
        missing = sorted(required - {selected})
        omitted += bool(missing)
        print(f"{headline} | {selected} | missing: {', '.join(missing) if missing else 'none'}")
    print(f"Examples with omitted label: {omitted}/{len(CASES)}")
