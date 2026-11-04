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
export type HistoricalStressPreset = Scenario & {
  window: string;
  start_date: string;
  end_date: string;
  basis: string;
  source_url: string;
};
export type Workstation = {
  portfolio_selections: { id: string; label: string; reference_date: string; construction: string; snapshot: DailySnapshot }[];
  historical_stress_presets: HistoricalStressPreset[];
  event_snapshots: EventSnapshot[];
  etf_portfolio: EtfPortfolio;
  etf_history: EtfHistory[];
  investigation: {
    default_date: string;
    disclosure: string;
    snapshots: DailySnapshot[];
  };
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
export type DailySnapshot = Omit<Workstation, "investigation" | "causal_mode" | "etf_portfolio" | "etf_history" | "event_snapshots" | "portfolio_selections">;
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

export type CausalRequest = { hypothesis: string; alternative: string; common_rates_bp: number; event_snapshot_id?: string };
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
  context: Pick<Reasoning["context"], "portfolio" | "market" | "daily" | "evidence"> & { event_reference?: EventSnapshot };
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

export type EtfPosition = {
  id: string; name: string; label: string; instrument: string;
  allocation_usd: number; weight_pct: number;
  source_url?: string; event_source_url?: string; exchange?: string; currency?: string; note?: string; eligible_from?: string;
  audit?: { minimum_data: string; recommendation: string; next_step: string };
};
export type EtfPortfolio = {
  reference_date: string; allocation_nav_usd: number; observed_nav_usd: null;
  basis: string; risk_basis: string; verified_on: string; positions: EtfPosition[];
};
export type EtfObservation = {
  date: string; close: number; currency: string; price_basis: string;
  source_url: string; bar_timestamp_utc: string;
  distribution_events: unknown[]; split_events: unknown[];
};
export type EtfHistory = {
  start: string; end: string; covered_allocation_usd: number;
  covered_price_pnl_usd: number | null; portfolio_pnl_usd: null;
  provider: string; retrieved_at: string; method: string;
  distribution_treatment: string; split_treatment: string;
  positions: (EtfPosition & {
    valuation: InstrumentValuation;
    status: string; reason: string; price_return_pct: number | null; price_pnl_usd: number | null;
    start_observation: EtfObservation | null; end_observation: EtfObservation | null;
  })[];
};

export type InstrumentValuation = {
  type: 'observed_security_close' | 'treasury_issue_price' | 'modeled_otc_mark' | 'cash_balance';
  status: 'available' | 'unavailable' | 'illustrative_only';
  unit: string; start_date: string; end_date: string;
  start_value: number | null; end_value: number | null;
  basis: string; source_urls: string[];
  reference_balance_usd?: number; reference_date?: string;
  treasury_review?: {
    checked_on: string; decision: string; source_qualification: string; reference_source_url: string;
    candidates: {
      cusip: string; coupon_pct: number; original_term: string;
      issue_date: string; maturity_date: string; terms_source_url: string; eligibility: string;
      reference_rows: { date: string; end_of_day_reference: string }[];
    }[];
  };
};

export type EventSnapshot = {
  id: string; title: string; start: string; end: string;
  euro_rate_change_bp?: number;
  euro_ig_spread_change_bp?: number;
  euro_hy_spread_change_bp?: number;
  start_nav_usd: number; end_nav_usd: number | null;
  estimated_pnl_usd: number | null; covered_pnl_usd: number; coverage_count: number;
  disclosure: string; causal_use: string; march_etf_retrieved_at: string;
  market_provenance: { provider: string; retrieved_at: string; timing: string };
  positions: {
    id: string; label: string; status: 'Estimated' | 'Unavailable';
    start_value_usd: number; end_value_usd: number | null; pnl_usd: number | null;
    method: string; assumptions: string[]; terms: Record<string, string | number>;
    inputs: { label: string; value: number; unit: string; status: string; source_url?: string | null }[];
  }[];
};
