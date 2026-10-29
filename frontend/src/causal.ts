import type { Calculation, CausalRequest, CausalResult, Shocks } from "./types";

export const demoHypotheses = ["Recession fears", "Inflation relief", "Liquidity and funding stress"];

export type CausalState = {
  hypothesis: string;
  alternative: string;
  commonRates: number;
  busy: boolean;
  calculating: boolean;
  error: string;
  result: CausalResult | null;
  drafts: Shocks[];
  calculations: Calculation[];
};
export const initialCausalState: CausalState = {
  hypothesis: "Recession fears", alternative: "Inflation relief", commonRates: -50,
  busy: false, calculating: false, error: "", result: null, drafts: [], calculations: [],
};

export function acceptProposals(state: CausalState, result: CausalResult): CausalState {
  return { ...state, result, busy: false, error: "", calculations: [],
    drafts: result.exploration.mechanisms.map(m => ({ ...m.proposed_shocks })) };
}
export function editAssumption(state: CausalState, index: number, factor: keyof Shocks, value: number): CausalState {
  return { ...state, error: "", calculations: [],
    drafts: state.drafts.map((draft, i) => i === index ? { ...draft, [factor]: value } : draft) };
}
export function causalRequest(state: CausalState, mode?: string): CausalRequest {
  if (mode === "demo" && [state.hypothesis, state.alternative].some(h => !demoHypotheses.includes(h))) throw new Error("Demo supports only the three named hypotheses. Custom hypotheses require live Meta mode.");
  if (!state.hypothesis.trim() || !state.alternative.trim()) throw new Error("Describe both economic hypotheses.");
  if (state.hypothesis.trim().toLowerCase() === state.alternative.trim().toLowerCase()) throw new Error("Choose two different hypotheses.");
  if (!Number.isFinite(state.commonRates) || Math.abs(state.commonRates) > 300) throw new Error("The shared yield assumption must be between −300 and +300bp.");
  return { hypothesis: state.hypothesis.trim(), alternative: state.alternative.trim(), common_rates_bp: state.commonRates };
}
