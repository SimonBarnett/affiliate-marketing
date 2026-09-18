/** Community Chest deck + lock. No DOM. */

import {
  PRINT_COST, AGM_TRUST_HIT, AGM_COMM_FLOOR, QR_TRAFFIC_MULT,
  AWIN_GMV_MULT, COOP_COST, ADS_ONLY_SPEND, ADS_ONLY_TRAFFIC,
  SUPPORT_CONV, BAD_REVIEW_CONV, CLUB_SHARE,
} from "./economy.js";
import { pick } from "./rng.js";

export function isHealthy(state) {
  if (state.clubs && state.clubs.length) {
    const live = state.clubs.some((c) => c.onboarded && !c.churned && c.partner && c.hasAudience);
    return !!(live && (state.intensity > 0));
  }
  return !!(state.partner && state.hasAudience && (state.intensity > 0));
}

export const DECK = [
  {
    id: "matchday_qr",
    seat: "club|partner",
    title: "Matchday QR",
    lesson: "QR on the programme only works if the catalogue is live, members are already there, and you promote that week.",
  },
  {
    id: "coach_link",
    seat: "club",
    title: "Coach puts the link in the group",
    lesson: "Contact templates the partner wrote are what make a coach share convert.",
  },
  {
    id: "flyers_no_url",
    seat: "club",
    title: "Flyers with no URL",
    lesson: "Print without a tracked link is spend the year cannot see. It never becomes a sale in this sim.",
  },
  {
    id: "seo_upsell",
    seat: "partner",
    title: "SEO upsell",
    lesson: "Ranking a club domain for product terms is a trap: Promote costs double and conversion falls.",
  },
  {
    id: "support_buy",
    seat: "club",
    title: "Support-your-club week",
    lesson: "Members buy where THEIR club earns — only if USP is on.",
  },
  {
    id: "awin_pause",
    seat: "platform",
    title: "Network pause",
    lesson: "A merchant going dark cuts tracked GMV until you remap. Print volume does not fill the hole.",
  },
  {
    id: "partner_ghost",
    seat: "club",
    title: "Partner goes quiet",
    lesson: "Without the partner, templates stop. Clubs do not invent the programme themselves.",
  },
  {
    id: "whatsapp_share",
    seat: "club",
    title: "WhatsApp share",
    lesson: "Shares only help if regular contact is already on.",
  },
  {
    id: "ads_only",
    seat: "club",
    title: "Boost the ads",
    lesson: "Bought clicks without an audience raise traffic and destroy margin.",
  },
  {
    id: "coop_week",
    seat: "platform",
    title: "Co-op week",
    lesson: "Platform money only discounts Promote if you are actually promoting.",
  },
  {
    id: "bad_review",
    seat: "club",
    title: "Bad review",
    lesson: "Conversion stays down until the partner's review template is in use.",
  },
  {
    id: "agm_vote",
    seat: "club",
    title: "AGM vote",
    lesson: "If the club has not seen commission, trust drops — especially with no partner story.",
  },
];

function addMod(state, mod) {
  state.modifiers = (state.modifiers || []).concat([mod]);
}

function applyFlyers(state) {
  state.money -= PRINT_COST;
  state.untrackedSpend = (state.untrackedSpend || 0) + PRINT_COST;
  state.untrackedPrintDelta = (state.untrackedPrintDelta || 0) + PRINT_COST;
  state.totalCosts += PRINT_COST;
}

export function applyCard(state, card, healthy, rng) {
  const id = typeof card === "string" ? card : card.id;
  const gmvBefore = state.totalRevenue;
  let note = "";

  if (id === "matchday_qr") {
    if (healthy && state.usp && state.partner) {
      addMod(state, { id: "qr", monthsLeft: 1, trafficMult: QR_TRAFFIC_MULT });
      note = "QR week: member traffic +40% this month.";
    } else {
      applyFlyers(state);
      note = "No live tracked link — those flyers are untracked spend.";
    }
  } else if (id === "coach_link") {
    if (healthy && state.contact) {
      addMod(state, { id: "coach", monthsLeft: 1, contactMult: 1.5 });
      note = "Coach share: contact is 1.5× this month.";
    } else note = "No contact templates in play — the share does nothing.";
  } else if (id === "flyers_no_url") {
    applyFlyers(state);
    note = "£/$" + PRINT_COST + " print with no URL. Zero tracked traffic.";
  } else if (id === "seo_upsell") {
    state.seo = true;
    if (!healthy) {
      addMod(state, { id: "seo_worse", monthsLeft: 12, convDelta: -0.5 });
      note = "SEO taken cold: trap is worse.";
    } else note = "SEO on. Promote will cost 2× and club-domain clicks convert poorly.";
  } else if (id === "support_buy") {
    if (healthy && state.usp) {
      addMod(state, { id: "support", monthsLeft: 1, convDelta: SUPPORT_CONV });
      note = "Support-your-club week: conversion spike.";
    } else note = "USP is off — members do not know the club earns.";
  } else if (id === "awin_pause") {
    const merch = (state.merchants || []).find((m) => m.live !== false);
    if (merch) {
      merch.live = false;
      note = merch.name + " paused. Category GMV ×0.7 until remapped.";
    } else {
      addMod(state, { id: "awin", monthsLeft: 99, gmvMult: AWIN_GMV_MULT });
      note = "Merchant paused. Category GMV ×0.7 until remapped.";
    }
  } else if (id === "partner_ghost") {
    if (state.partner) {
      state.contact = false;
      state.content = false;
      state.churnRisk = (state.churnRisk || 0) + 1;
      note = "Templates off. Partner went quiet.";
    } else note = "No partner was live anyway.";
  } else if (id === "whatsapp_share") {
    if (healthy && state.contact) {
      addMod(state, { id: "wa", monthsLeft: 1, trafficAdd: 8 });
      note = "Share lands because contact is already on.";
    } else note = "Nobody is on the list — the forward dies.";
  } else if (id === "ads_only") {
    addMod(state, { id: "ads", monthsLeft: 1, trafficAdd: ADS_ONLY_TRAFFIC });
    state.money -= ADS_ONLY_SPEND;
    state.totalAdspend += ADS_ONLY_SPEND;
    state.totalPaidSearch += ADS_ONLY_SPEND;
    state.totalCosts += ADS_ONLY_SPEND;
    if (!healthy) {
      // Unhealthy ads still buy a handful of cold sales (GMV gift) but margin is worse.
      const gift = 40;
      state.totalRevenue += gift;
      const comm = gift * 0.2 * 0.9;
      state.totalCommission += comm;
      state.money += comm * CLUB_SHARE;
      state.salesCount += 1;
      note = "Ads without audience: a bit of GMV, a lot of spend.";
    } else note = "Paid boost on top of members — still paid to Google.";
  } else if (id === "coop_week") {
    state.money -= COOP_COST;
    state.totalCosts += COOP_COST;
    if (healthy && state.intensity > 0) {
      addMod(state, { id: "coop", monthsLeft: 1, promoteCpcMult: 0.7 });
      note = "Co-op paid. Promote is cheaper this month.";
    } else note = "Co-op invoice landed; no Promote, so no discount.";
  } else if (id === "bad_review") {
    if (state.reviews) note = "Reviews template already live — the hit is contained.";
    else {
      addMod(state, { id: "badrev", monthsLeft: 12, convDelta: BAD_REVIEW_CONV, untilReviews: true });
      note = "Conversion down until reviews are on.";
    }
  } else if (id === "agm_vote") {
    const ytd = (state.totalCommission || 0) * CLUB_SHARE;
    if (!healthy || ytd < AGM_COMM_FLOOR) {
      state.trust = (state.trust == null ? 60 : state.trust) - AGM_TRUST_HIT;
      note = "AGM: trust −15. The club has not seen enough commission.";
    } else note = "AGM holds. Enough commission is on the board.";
  } else {
    note = "Unknown card.";
  }

  return {
    id,
    healthy: !!healthy,
    gmvDelta: state.totalRevenue - gmvBefore,
    note,
  };
}

export function drawChest(state, rng, month) {
  const card = pick(DECK, rng);
  const healthy = isHealthy(state);
  const result = applyCard(state, card, healthy, rng);
  state.chestDrawnMonth = month;
  state.pendingChest = { card, healthy, result };
  return state.pendingChest;
}

export function shouldDrawChest(state, month) {
  if (!state || state.ended) return false;
  return state.chestDrawnMonth !== month;
}

export function tickModifiers(state) {
  const mods = state.modifiers || [];
  const next = [];
  for (const m of mods) {
    if (m.untilReviews && state.reviews) continue;
    const left = (m.monthsLeft || 1) - 1;
    if (left > 0) next.push(Object.assign({}, m, { monthsLeft: left }));
  }
  state.modifiers = next;
}

export function modsOf(state) {
  return state.modifiers || [];
}
