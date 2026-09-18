import { test } from "node:test";
import assert from "node:assert/strict";
import {
  createState, saleGmv, pauseMerchant, remapMerchant, defaultMerchants,
  qualityScore, platformWon, platformTake, spendCoop,
} from "../sim/kernel.js";
import { AWIN_GMV_MULT, COOP_COST } from "../sim/economy.js";

test("AT9 Awin pause cuts category GMV until remap restores", () => {
  const st = createState({
    partner: true,
    merchants: defaultMerchants(),
    products: [{ name: "Shirt", price: 100, commission_rate: 0.2, category: "kit" }],
  });
  const prod = st.products[0];
  assert.equal(saleGmv(st, prod), 100);
  pauseMerchant(st, "kit");
  assert.equal(saleGmv(st, prod), 100 * AWIN_GMV_MULT);
  remapMerchant(st, "kit");
  assert.equal(saleGmv(st, prod), 100);
});

test("quality score has no print-volume term", () => {
  const st = createState({
    partner: true, hasAudience: true, usp: true, intensity: 50,
    untrackedSpend: 9999, printDigital: "print",
  });
  const q = qualityScore(st);
  const st2 = createState({
    partner: true, hasAudience: true, usp: true, intensity: 50,
    untrackedSpend: 0, printDigital: "digital",
  });
  assert.equal(q, qualityScore(st2));
  assert.ok(q > 0);
});

test("platform win needs take and audience GMV share >= 0.5", () => {
  const st = createState({ partner: true, hasAudience: true });
  st.totalCommission = 400;
  st.totalRevenue = 1000;
  st.totalRevenueAudience = 600;
  assert.ok(platformTake(st) > 0);
  assert.equal(platformWon(st), true);
  st.totalRevenueAudience = 100;
  assert.equal(platformWon(st), false);
});

test("coop spend only discounts when promoting", () => {
  const idle = createState({ intensity: 0, coopBudget: 200 });
  assert.equal(spendCoop(idle), true);
  assert.equal(idle.coopBudget, 200 - COOP_COST);
  assert.equal((idle.modifiers || []).some((m) => m.id === "coop"), false);
  const busy = createState({ intensity: 40, coopBudget: 200 });
  spendCoop(busy);
  assert.equal((busy.modifiers || []).some((m) => m.id === "coop"), true);
});
