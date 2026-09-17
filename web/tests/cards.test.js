import { test } from "node:test";
import assert from "node:assert/strict";
import { createRng } from "../sim/rng.js";
import { createState, communityShare } from "../sim/kernel.js";
import { DECK, applyCard, isHealthy } from "../sim/cards.js";

const base = {
  partner: false,
  hasAudience: false,
  seo: false,
  contact: false,
  content: false,
  paidSearch: false,
  usp: false,
  reviews: false,
  intensity: 0,
  products: [{ name: "Widget", price: 20, commission_rate: 0.2 }],
};

test("AT5 every chest card with healthy=false does not gift GMV except ads_only", () => {
  const rng = createRng(99);
  assert.equal(isHealthy(createState(base)), false);
  for (const card of DECK) {
    const st = createState(base);
    st.money = 1000;
    const gmv0 = st.totalRevenue;
    const share0 = communityShare(st);
    const result = applyCard(st, card, false, rng);
    if (card.id === "ads_only") {
      assert.ok(communityShare(st) <= share0, card.id + " must hurt margin");
    } else {
      assert.ok(st.totalRevenue <= gmv0 + 1e-9, card.id + " gifted GMV when lock broken: " + (st.totalRevenue - gmv0));
    }
    assert.equal(result.healthy, false);
  }
});

test("healthy QR does not print-spend", () => {
  const st = createState({
    ...base, partner: true, hasAudience: true, usp: true, intensity: 40,
  });
  applyCard(st, "matchday_qr", true, createRng(1));
  assert.equal(st.untrackedSpend || 0, 0);
  assert.ok((st.modifiers || []).some((m) => m.id === "qr"));
});
