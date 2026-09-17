/**
 * Month ledger + debrief copy. No DOM.
 *
 * uspOffCommissionLost: only when audience is on and USP is off.
 * Actual capture is 0.65; counterfactual 1.0.
 * lost = actualGrossCommission * (1 / 0.65 - 1).
 * No audience → 0 (cold capture is not the USP lesson).
 */

import { CAPTURE_AUDIENCE, PROMOTE_LOW } from "./economy.js";

export const LS_LEDGER = "am_last_ledger_v1";

export function emptyMonthMark() {
  return {
    sales: 0,
    commission: 0,
    gmv: 0,
    promote: 0,
    paidSearch: 0,
    maxIntensity: 0,
  };
}

export function closeMonth(state, month) {
  const mark = state.monthMark || emptyMonthMark();
  const uspOn = !!state.usp;
  const clubCommission = (state.totalCommission - mark.commission) * 0.25;
  const paidSearchSpend = state.totalPaidSearch - mark.paidSearch;
  const promoteSpend = state.totalPromote - mark.promote;
  const gmv = state.totalRevenue - mark.gmv;
  const sales = state.salesCount - mark.sales;
  const monthGross = state.totalCommission - mark.commission;
  let uspOffCommissionLost = 0;
  if (state.hasAudience && !uspOn && monthGross > 0) {
    uspOffCommissionLost = monthGross * (1 / CAPTURE_AUDIENCE - 1);
  }
  const row = {
    month,
    promoteIntensity: mark.maxIntensity,
    sales,
    untrackedPrint: state.untrackedPrintDelta || 0,
    uspOn,
    clubCommission,
    paidSearchSpend,
    promoteSpend,
    gmv,
    uspOffCommissionLost,
  };
  state.untrackedPrintDelta = 0;
  state.ledger = (state.ledger || []).concat([row]);
  state.monthMark = {
    sales: state.salesCount,
    commission: state.totalCommission,
    gmv: state.totalRevenue,
    promote: state.totalPromote,
    paidSearch: state.totalPaidSearch,
    maxIntensity: state.intensity || 0,
  };
  return row;
}

export function noteIntensity(state) {
  if (!state.monthMark) state.monthMark = emptyMonthMark();
  state.monthMark.maxIntensity = Math.max(state.monthMark.maxIntensity || 0, state.intensity || 0);
}

export function ledgerTotals(ledger) {
  const rows = ledger || [];
  const untrackedPrint = rows.reduce((a, r) => a + (r.untrackedPrint || 0), 0);
  const promoteSpend = rows.reduce((a, r) => a + (r.promoteSpend || 0), 0);
  const paidSearchSpend = rows.reduce((a, r) => a + (r.paidSearchSpend || 0), 0);
  const uspOffCommissionLost = rows.reduce((a, r) => a + (r.uspOffCommissionLost || 0), 0);
  const spend = untrackedPrint + promoteSpend + paidSearchSpend;
  const untrackedPct = spend > 0 ? (100 * untrackedPrint) / spend : 0;
  const lowPromoteMonths = rows.filter((r) => (r.promoteIntensity || 0) < PROMOTE_LOW).map((r) => r.month);
  return {
    monthsPlayed: rows.length,
    untrackedPrint,
    untrackedPct,
    uspOffCommissionLost,
    lowPromoteMonths,
    spend,
  };
}

export function debriefSentences(ledger) {
  const t = ledgerTotals(ledger);
  const months = t.lowPromoteMonths;
  const monthList = months.length ? months.map((m) => "M" + m).join(", ") : "none";
  return [
    months.length
      ? `Promote was low in ${months.length} month${months.length === 1 ? "" : "s"} (${monthList}).`
      : "Promote stayed on through the year.",
    t.spend <= 0
      ? "No marketing spend to split — nothing untracked."
      : `${Math.round(t.untrackedPct)}% of spend was untracked print (catalogues without a tracked link).`,
    t.uspOffCommissionLost > 0.5
      ? `About $${Math.round(t.uspOffCommissionLost).toLocaleString()} of commission was left on the table while USP was off.`
      : "USP framing did not leak commission this year.",
  ];
}
