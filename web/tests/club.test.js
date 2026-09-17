import { test } from "node:test";
import assert from "node:assert/strict";
import { createRng } from "../sim/rng.js";
import {
  createState, runYear, getConversion, applyPrintPack, tickTrust,
  highScoreEligible, communityShare,
} from "../sim/kernel.js";
import { TRUST_START } from "../sim/economy.js";

const widget = [{ name: "Widget", price: 20, commission_rate: 0.2 }];

test("AT1 print-only year: no high score, untracked spend, no print sales", () => {
  const st = createState({
    partner: false, hasAudience: false, usp: false, intensity: 20, products: widget,
  });
  applyPrintPack(st);
  runYear(st, createRng(3));
  assert.ok(st.untrackedSpend > 0);
  assert.equal(st.salesCount, 0, "print does not create sales");
  assert.equal(highScoreEligible(st), false);
});

test("AT2 healthy year beats print-only clubCommission", () => {
  const print = createState({ partner: false, hasAudience: false, usp: false, intensity: 20, products: widget });
  applyPrintPack(print);
  runYear(print, createRng(3));
  const healthy = createState({
    partner: true, hasAudience: true, usp: true, contact: true, content: true, reviews: true,
    intensity: 40, products: widget,
  });
  runYear(healthy, createRng(3));
  const printClub = print.totalCommission * 0.25;
  const healthyClub = healthy.totalCommission * 0.25;
  assert.ok(healthyClub > printClub, "healthy " + healthyClub + " vs print " + printClub);
});

test("AT7 trust <30 haircuts conversion; spam without offers drops trust", () => {
  const flags = {
    partner: true, hasAudience: true, usp: false, contact: true, reviews: false,
    intensity: 20, products: widget,
  };
  const low = createState({ ...flags, trust: 20 });
  const ok = createState({ ...flags, trust: 60 });
  assert.ok(getConversion(low) < getConversion(ok) - 0.01);
  const spam = createState({ ...flags, trust: TRUST_START });
  const before = spam.trust;
  tickTrust(spam);
  assert.ok(spam.trust < before, "spam contact without USP must drop trust");
});

test("AT10 high-score skipped when lesson lock broken", () => {
  const broken = createState({ partner: true, hasAudience: true, usp: false, products: widget });
  assert.equal(highScoreEligible(broken), false);
  const locked = createState({ partner: true, hasAudience: true, usp: true, products: widget });
  assert.equal(highScoreEligible(locked), true);
});
