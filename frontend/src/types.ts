export type Shocks = {
  rates_bp: number;
  ig_bp: number;
  hy_bp: number;
  equity_pct: number;
  fx_pct: number;
};
export type Position = {
  id: string;
  name: string;
  asset_class: string;
  instrument: string;
  market_value_usd: number;
  notional_usd: number;
  dv01_usd_per_bp: number;
  cs01_usd_per_bp: number;
  equity_delta_usd: number;
  fx_delta_usd: number;
  pnl_usd: number;
  rates_pnl: number;
  credit_pnl: number;
  equity_pnl: number;
  fx_pnl: number;
};
export type Calculation = {
  shocks: Shocks;
  total_pnl_usd: number;
  pnl_pct_nav: number;
  by_factor: Record<string, number>;
  by_asset_class: { asset_class: string; pnl_usd: number }[];
  positions: Position[];
  method: string;
};
export type Episode = {
  id: string;
  title: string;
  period: string;
  fact: string;
  interpretation: string;
  limitation: string;
  source_title: string;
  source_url: string;
};
export type Scenario = {
  id: string;
  name: string;
  description: string;
  shocks: Shocks;
};
export type Workstation = {
  causal_mode: string;
  portfolio_name: string;
  data_kind: string;
  nav_usd: number;
  opening_nav_usd: number;
  daily_return_pct: number;
  positions: Position[];
  allocation: { asset_class: string; market_value_usd: number }[];
  exposures: {
    dv01_usd_per_bp: number;
    cs01_usd_per_bp: number;
    ig_cs01_usd_per_bp: number;
    hy_cs01_usd_per_bp: number;
    equity_delta_usd: number;
    fx_delta_usd: number;
  };
  daily: Calculation;
  market: {
    as_of: string;
    previous_date: string;
    label: string;
    commentary: string;
    yields: { tenor: string; previous_pct: number; current_pct: number }[];
    credit: { name: string; level_bp: number; change_bp: number }[];
    equities: { name: string; change_pct: number }[];
    fx: { name: string; level: number; change_pct: number }[];
  };
  scenarios: Scenario[];
  history: Episode[];
};
export type Reasoning = {
  investigation_id: string;
  investigation_scope: "daily" | "scenario" | "historical";
  verification?: ClaimVerdict[];
  investigation_focus?: "daily" | "scenario" | "historical" | "question";
  question: string;
  mode: string;
  model: string | null;
  interpretation: {
    hypotheses?: {
      title: string;
      mechanism: string;
      consistent_evidence: string;
      portfolio_implications?: string;
      uncertainty: string;
      available_checks: string;
      additional_evidence: string;
    }[];
    financial_claims?: FinancialClaim[];
    summary: string;
    principal_risk_observations: string[];
    economic_interpretation: string;
    historical_analogies: string[];
    potential_vulnerabilities: string[];
    assumptions_and_uncertainties: string[];
    evidence_references: string[];
  };
  context: {
    portfolio: Pick<
      Workstation,
      "portfolio_name" | "nav_usd" | "positions" | "exposures"
    >;
    historical?: {
      episode: string;
      credit_spreads_included?: boolean;
      observations: {
        ust10: { previous_yield_pct: number; current_yield_pct: number };
        ust2: { previous_yield_pct: number; current_yield_pct: number };
        sp500: { reported_return_pct: number };
        eurusd: { reported_return_pct: number };
        ig_spread?: { previous_spread_bp?: number; current_spread_bp?: number; change_bp: number | null };
        hy_spread?: { previous_spread_bp?: number; current_spread_bp?: number; change_bp: number | null };
      };
      mapping_assumptions: string[];
      coverage: string;
      sources: Record<string, { description: string; url: string }>;
    };
    macro_context?: { cutoff: string; facts: { source: string; text: string }[] };
    daily: Calculation;
    market: Workstation["market"];
    scenario: Calculation;
    evidence: { id: string; description: string; url?: string }[];
    [key: string]: unknown;
  };
  context_operations: { operation: string; source: string }[];
};

export type CausalRequest = { hypothesis: string; alternative: string; common_rates_bp: number };
export type CausalMechanism = {
  title: string;
  economic_mechanism: string;
  cross_asset: Record<keyof Shocks, { direction: "up" | "down" | "unchanged" | "ambiguous"; rationale: string }>;
  proposed_shocks: Shocks;
  assumption_note: string;
  alternative_explanations: string[];
  discriminating_evidence: string[];
  uncertainty: string[];
  evidence_references: string[];
};
export type CausalResult = {
  request: CausalRequest;
  mode: string;
  model: string | null;
  usage: Record<string, number> | null;
  exploration: { mechanisms: CausalMechanism[] };
  context: Pick<Reasoning["context"], "portfolio" | "market" | "daily" | "evidence">;
};

export type FinancialClaim = {
  statement: string;
  kind: string;
  period: string;
  target: string;
  metric: string;
  assertion: string;
  value: number | null;
  rounding: string;
  components: string[];
};
export type ClaimVerdict = {
  claim: FinancialClaim;
  mapping: string;
  verdict: "Verified" | "Contradicted" | "Not established" | "Not checked";
  explanation: string;
  evidence: { path: string; value: number | string }[];
  limitations: string[];
  original_wording_status: "Not checked";
};
