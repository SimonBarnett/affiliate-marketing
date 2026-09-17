/** Pure year engine. No DOM, no canvas. */

import {
  MONTHLY_COST, ADSPEND_MONTHLY_CAP, ADSPEND_HARD_CAP, PAID_SEARCH_DAILY,
  CONTACT_ENGAGEMENT_BONUS, CONTACT_TRAFFIC_BONUS,
  SEO_TRAFFIC_POINTS, SEO_TRAFFIC_CLUB, SEO_CLUB_CONV_HAIRCUT,
  CPC_BASE, AUDIENCE_CPC, VISITORS_PER_INTENSITY,
  DAYS_PER_MONTH, TOTAL_DAYS, MIN_WORTH_IT, ACCEPTABLE_DECLINE,
  EARLY_CONTRACT_LOSS, CLUB_SHARE, CAPTURE_USP, CAPTURE_AUDIENCE, CAPTURE_COLD,
  PAID_SEARCH_TRAFFIC,
} from "./economy.js";
import { pick, rnd } from "./rng.js";
import { closeMonth, emptyMonthMark, noteIntensity } from "./ledger.js";

export { TOTAL_DAYS, DAYS_PER_MONTH };

export function createState(opts) {
  opts = opts || {};
  const tactics = opts.conversion || {};
  return {
    partner: !!opts.partner,
    hasAudience: !!opts.hasAudience,
    seo: !!opts.seo,
    contact: !!opts.contact,
    content: !!opts.content,
    paidSearch: !!(opts.paidSearch || tactics["Paid search"]),
    usp: !!(opts.usp || tactics["My club get the commission"]),
    reviews: !!(opts.reviews || tactics["Product reviews"]),
    intensity: opts.intensity || 0,
    products: (opts.products || []).slice(),
    day: 0,
    money: 0,
    totalRevenue: 0,
    totalCommission: 0,
    totalAdspend: 0,
    totalPromote: 0,
    totalPaidSearch: 0,
    totalCosts: 0,
    salesCount: 0,
    lastMonthCharged: 0,
    monthlyAdspend: 0,
    untrackedPrintDelta: 0,
    untrackedSpend: 0,
    ledger: [],
    monthMark: emptyMonthMark(),
    ended: false,
    endReason: null,
    yearsCompleted: opts.yearsCompleted || 0,
    lastYearNet: opts.lastYearNet == null ? null : opts.lastYearNet,
  };
}

export function dayToDate(d) {
  let rem = d;
  for (let mi = 0; mi < DAYS_PER_MONTH.length; mi++) {
    if (rem < DAYS_PER_MONTH[mi]) return { mi, dom: rem + 1 };
    rem -= DAYS_PER_MONTH[mi];
  }
  return { mi: 11, dom: 25 };
}

export function currentMonth(state) {
  return dayToDate(Math.min(state.day, TOTAL_DAYS - 1)).mi + 1;
}

export function paidSearchOn(state) { return !!state.paidSearch; }
export function uspOn(state) { return !!state.usp; }

export function getConversion(state) {
  let base = 1.0, other = 0, clubBonus = 0, clubOn = !!state.usp;
  if (state.paidSearch) other += 1.5;
  if (state.reviews) other += 2.0;
  if (state.contact && state.hasAudience) other += CONTACT_ENGAGEMENT_BONUS;
  if (clubOn) clubBonus = 1.0;
  let conv = clubOn ? base + clubBonus + other * 2.0 : base + other;
  if (state.seo && state.hasAudience) conv = Math.max(0.5, conv - SEO_CLUB_CONV_HAIRCUT);
  return conv;
}

export function getTrafficPotential(state) {
  let seoT = 0;
  if (state.seo) {
    seoT = state.hasAudience ? SEO_TRAFFIC_CLUB : SEO_TRAFFIC_POINTS;
    if (state.partner && !state.hasAudience) seoT *= 1.25;
  }
  let paidT = paidSearchOn(state) ? PAID_SEARCH_TRAFFIC : 0;
  if (paidSearchOn(state) && state.partner) paidT *= 1.15;
  const intensity = state.intensity || 0;
  if (state.hasAudience) {
    let organic = 25, strat = 0;
    if (state.content) strat += 14;
    if (state.contact) strat += CONTACT_TRAFFIC_BONUS;
    let promo;
    if (state.partner) { strat *= 2; promo = intensity * 0.5; }
    else promo = intensity * 0.35;
    return Math.max(0, Math.min(100, organic + strat + promo + seoT + paidT));
  }
  const promo = intensity * (state.partner ? 1.5 : 1.0);
  return Math.max(0, Math.min(100, promo + seoT + paidT));
}

export function getTraffic(state) {
  let base = getTrafficPotential(state);
  if (state.hasAudience && !state.partner) base = Math.max(0, base - 12.5);
  return Math.max(0, Math.min(100, base));
}

export function trafficWithIntensity(state, sim) {
  const saved = state.intensity;
  state.intensity = sim;
  const t = getTraffic(state);
  state.intensity = saved;
  return t;
}

export function getCommissionCapture(state) {
  if (state.usp && state.hasAudience) return CAPTURE_USP;
  if (state.hasAudience) return CAPTURE_AUDIENCE;
  return CAPTURE_COLD;
}

export function promoteCpc(state) {
  let cpc = state.hasAudience ? AUDIENCE_CPC : CPC_BASE;
  if (state.partner) cpc *= 0.65;
  if (state.seo || paidSearchOn(state)) cpc *= 2;
  return cpc;
}

export function communityShare(state) {
  const fee = Math.max(0, state.totalCosts - state.totalAdspend);
  return state.totalCommission * CLUB_SHARE - state.totalAdspend - fee;
}

export function tryAutoSale(state, rng) {
  if (!state.partner || !state.products.length) return null;
  const conv = getConversion(state), traffic = getTraffic(state);
  const visitors = (traffic / 100) * 40;
  const expected = visitors * (conv / 100);
  const p = Math.min(0.92, expected);
  if (rng.next() >= p) return null;
  const prod = pick(state.products, rng);
  const rate = prod.commission_rate;
  const commission = prod.price * rate * getCommissionCapture(state);
  state.totalRevenue += prod.price;
  state.totalCommission += commission;
  const clubEarn = commission * CLUB_SHARE;
  state.money += clubEarn;
  state.salesCount += 1;
  return { name: prod.name, price: prod.price, rate, commission, clubEarn, product: prod };
}

function chargePaidSearch(state) {
  if (!paidSearchOn(state)) return;
  const rem = Math.max(0, ADSPEND_HARD_CAP - state.monthlyAdspend);
  const daily = PAID_SEARCH_DAILY * (state.partner ? 0.75 : 1);
  const ps = Math.min(daily, rem);
  if (ps > 0) {
    state.money -= ps;
    state.totalAdspend += ps;
    state.totalPaidSearch += ps;
    state.totalCosts += ps;
    state.monthlyAdspend += ps;
  }
}

function chargePromote(state) {
  if (!(state.intensity > 1)) return;
  const visitors = state.intensity * VISITORS_PER_INTENSITY;
  let spend = visitors * promoteCpc(state);
  const cap = state.hasAudience ? Math.min(ADSPEND_MONTHLY_CAP, ADSPEND_HARD_CAP) : ADSPEND_HARD_CAP;
  const rem = Math.max(0, cap - state.monthlyAdspend);
  spend = Math.min(spend, rem);
  if (state.hasAudience && rem > 0 && spend < 0.05) spend = Math.min(0.05, rem);
  if (spend > 0) {
    state.money -= spend;
    state.totalAdspend += spend;
    state.totalPromote += spend;
    state.totalCosts += spend;
    state.monthlyAdspend += spend;
  }
}

export function stepDay(state, rng) {
  if (state.ended) return { sale: null, ended: true };
  state.day += 1;
  noteIntensity(state);
  chargePaidSearch(state);
  chargePromote(state);
  const sale = tryAutoSale(state, rng);
  const m = currentMonth(state);
  if (m > state.lastMonthCharged && m <= 12) {
    if (state.lastMonthCharged >= 1) closeMonth(state, state.lastMonthCharged);
    if (state.partner) {
      state.money -= MONTHLY_COST;
      state.totalCosts += MONTHLY_COST;
    }
    state.lastMonthCharged = m;
    state.monthlyAdspend = 0;
    state.monthMark.maxIntensity = state.intensity || 0;
  }
  if (state.money < EARLY_CONTRACT_LOSS) {
    finalizeYearAccounts(state, rng);
    closeRemaining(state);
    state.ended = true;
    state.endReason = "early_loss";
    return { sale, ended: true, endReason: "early_loss" };
  }
  if (state.day >= TOTAL_DAYS) {
    finalizeYearAccounts(state, rng);
    closeRemaining(state);
    state.ended = true;
    state.endReason = "year_end";
    return { sale, ended: true, endReason: "year_end" };
  }
  return { sale, ended: false };
}

function closeRemaining(state) {
  const last = state.lastMonthCharged || currentMonth(state);
  const already = (state.ledger || []).some((r) => r.month === last);
  if (!already && last >= 1) closeMonth(state, last);
}

export function runYear(state, rng) {
  while (!state.ended) stepDay(state, rng);
  return state;
}

export function endRun(state, rng) {
  if (state.ended) return state;
  finalizeYearAccounts(state, rng);
  closeRemaining(state);
  state.ended = true;
  if (!state.endReason) state.endReason = "year_end";
  return state;
}

export function finalizeYearAccounts(state, rng) {
  const ytdSales = state.salesCount, ytdRev = state.totalRevenue, ytdComm = state.totalCommission;
  const ytdAd = state.totalAdspend, ytdCosts = state.totalCosts, ytdMoney = state.money;
  const daysDone = Math.max(0, Math.min(state.day, TOTAL_DAYS));
  const remaining = Math.max(0, TOTAL_DAYS - daysDone);
  const avgPromo = 30;
  const traffic = state.partner ? trafficWithIntensity(state, avgPromo) : 0;
  const conv = state.partner ? Math.max(0.5, getConversion(state)) : 0;
  const expectedPerDay = (traffic / 100) * 40 * (conv / 100);
  const nRem = Math.max(0, Math.round(expectedPerDay * remaining * rnd(rng, 0.92, 1.08)));
  let extraRev = 0, extraComm = 0, extraSales = 0;
  const fallback = state.products.length ? state.products : [{ price: 29.99, commission_rate: 0.2 }];
  for (let i = 0; i < nRem; i++) {
    const prod = pick(fallback, rng);
    const commission = prod.price * (prod.commission_rate || 0.2) * getCommissionCapture(state);
    extraComm += commission; extraRev += prod.price; extraSales++;
  }
  let cpc = state.hasAudience
    ? AUDIENCE_CPC * (state.partner ? 0.65 : 1)
    : CPC_BASE * (state.partner ? 0.65 : 1);
  if (state.seo || paidSearchOn(state)) cpc *= 2;
  const visitors = avgPromo * VISITORS_PER_INTENSITY;
  const monthsLeft = Math.max(1, 12 - state.lastMonthCharged);
  const monthlyCap = state.hasAudience ? ADSPEND_MONTHLY_CAP : ADSPEND_HARD_CAP;
  const promoteRest = Math.min(visitors * cpc * remaining * 0.35, monthlyCap * monthsLeft);
  let psRest = 0;
  if (paidSearchOn(state) && remaining > 0) {
    const daily = PAID_SEARCH_DAILY * (state.partner ? 0.75 : 1);
    psRest = Math.min(daily * remaining, ADSPEND_HARD_CAP * monthsLeft);
  }
  let partnerRest = 0;
  if (state.partner && 12 - state.lastMonthCharged > 0) partnerRest = MONTHLY_COST * (12 - state.lastMonthCharged);

  if (daysDone === 0 && ytdSales === 0) {
    state.salesCount = 0; state.totalRevenue = 0; state.totalCommission = 0;
    state.totalAdspend = 0; state.totalPromote = 0; state.totalPaidSearch = 0; state.totalCosts = 0; state.money = 0;
    const nFull = Math.max(0, Math.round(expectedPerDay * TOTAL_DAYS * rnd(rng, 0.92, 1.08)));
    for (let i = 0; i < nFull; i++) {
      const prod = pick(fallback, rng);
      const commission = prod.price * (prod.commission_rate || 0.2) * getCommissionCapture(state);
      state.totalRevenue += prod.price; state.totalCommission += commission;
      state.money += commission * CLUB_SHARE; state.salesCount++;
    }
    let promoYear = Math.min(visitors * cpc * TOTAL_DAYS * 0.35, monthlyCap * 12);
    if (state.seo || paidSearchOn(state)) promoYear *= 2;
    state.money -= promoYear; state.totalAdspend += promoYear; state.totalPromote += promoYear; state.totalCosts += promoYear;
    if (paidSearchOn(state)) {
      const ps = Math.min(PAID_SEARCH_DAILY * (state.partner ? 0.75 : 1) * TOTAL_DAYS, ADSPEND_HARD_CAP * 12);
      state.money -= ps; state.totalAdspend += ps; state.totalPaidSearch += ps; state.totalCosts += ps;
    }
    if (state.partner) { const fee = MONTHLY_COST * 12; state.money -= fee; state.totalCosts += fee; }
  } else {
    state.salesCount = ytdSales + extraSales;
    state.totalRevenue = ytdRev + extraRev;
    state.totalCommission = ytdComm + extraComm;
    state.totalAdspend = ytdAd + promoteRest + psRest;
    state.totalPromote += promoteRest;
    state.totalPaidSearch += psRest;
    state.totalCosts = ytdCosts + promoteRest + psRest + partnerRest;
    state.money = ytdMoney + extraComm * CLUB_SHARE - promoteRest - psRest - partnerRest;
  }
  state.lastMonthCharged = 12;
  state.day = TOTAL_DAYS;
  state.monthlyAdspend = 0;
}

export function pnlDecision(state) {
  const net = communityShare(state);
  let lost = false, lossReason = null, disappointment = false;
  if (state.endReason === "early_loss") {
    lost = true; lossReason = "early_loss";
  } else if (net < 0) {
    lost = true; lossReason = "loss";
  } else if (state.yearsCompleted >= 1 && net < MIN_WORTH_IT) {
    lost = true; lossReason = "not_worth";
  }
  if (state.yearsCompleted >= 1 && state.lastYearNet != null) {
    const prev = state.lastYearNet;
    if (prev > 0 && net < prev) {
      const floor = prev * (1 - ACCEPTABLE_DECLINE);
      if (net < floor) { lost = true; lossReason = "worse_than_last"; }
      else if (!lost) disappointment = true;
    } else if (prev <= 0 && net < prev) { lost = true; lossReason = "worse_than_last"; }
  }
  return { net, lost, lossReason, disappointment };
}
