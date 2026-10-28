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
  question: string;
  mode: string;
  model: string | null;
  interpretation: {
    summary: string;
    principal_risk_observations: string[];
    economic_interpretation: string;
    historical_analogies: string[];
    potential_vulnerabilities: string[];
    assumptions_and_uncertainties: string[];
    evidence_references: string[];
  };
  context: {
    scenario: Calculation;
    evidence: { id: string; description: string; url?: string }[];
    [key: string]: unknown;
  };
  context_operations: { operation: string; source: string }[];
};
