import { test } from "node:test";
import assert from "node:assert/strict";
import { createRng } from "../sim/rng.js";
import {
  createState, createClub, onboardClub, stepDay, tickChurn,
  liveCatalogue, partnerWon, partnerProfit, highScoreEligible, TOTAL_DAYS,
} from "../sim/kernel.js";

const widget = [{ name: "Widget", price: 20, commission_rate: 0.2 }];

test("AT8 two zero-promote months churn a live catalogue club", () => {
  const club = createClub({ id: "a", name: "Test RFC", products: widget });
  onboardClub(club, "catalogue");
  club.hasAudience = true;
  club.usp = true;
  const st = createState({ seat: "partner", products: widget, clubs: [club], intensity: 0 });
  const rng = createRng(1);
  let churnedOn = null;
  for (let i = 0; i < 90 && !st.ended; i++) {
    stepDay(st, rng);
    if (st.clubs[0].churned) { churnedOn = st.day; break; }
  }
  assert.ok(st.clubs[0].churned, "club must churn after two zero-promote months");
  assert.ok(churnedOn >= 50 && churnedOn <= 70, "churn around month 3 start, got day " + churnedOn);
});

test("partner win needs profit, >=2 live USP clubs", () => {
  const a = createClub({ id: "a", name: "A", products: widget });
  const b = createClub({ id: "b", name: "B", products: widget });
  onboardClub(a, "catalogue"); onboardClub(b, "catalogue");
  a.hasAudience = true; a.usp = true; a.share = 1;
  b.hasAudience = true; b.usp = true; b.share = 1;
  const st = createState({ seat: "partner", products: widget, clubs: [a, b], intensity: 40 });
  const rng = createRng(2);
  for (let i = 0; i < TOTAL_DAYS && !st.ended; i++) stepDay(st, rng);
  assert.ok(liveCatalogue(st).length >= 2);
  assert.equal(liveCatalogue(st).every((c) => c.usp), true);
  assert.ok(partnerProfit(st) > 0);
  assert.equal(partnerWon(st), true);
  assert.equal(highScoreEligible(st), true);
});

test("print-only club in portfolio blocks high score", () => {
  const a = createClub({ id: "a", name: "A", products: widget });
  const b = createClub({ id: "b", name: "B", products: widget });
  onboardClub(a, "catalogue");
  onboardClub(b, "print");
  a.hasAudience = true; a.usp = true;
  const st = createState({ seat: "partner", products: widget, clubs: [a, b], intensity: 20 });
  assert.equal(highScoreEligible(st), false);
});
