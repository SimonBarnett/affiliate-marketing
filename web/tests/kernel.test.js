import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createRng } from "../sim/rng.js";
import {
  createState, getConversion, getTraffic, promoteCpc, communityShare,
  runYear, TOTAL_DAYS,
} from "../sim/kernel.js";

const here = dirname(fileURLToPath(import.meta.url));
const load = (name) => JSON.parse(readFileSync(join(here, "fixtures", name), "utf8"));
const seoAudience = load("seo-audience.json");
const paidCold = load("paid-search-cold.json");

test("AT0 kernel has no document", () => {
  const dir = join(here, "../sim");
  for (const name of readdirSync(dir)) {
    if (!name.endsWith(".js")) continue;
    const src = readFileSync(join(dir, name), "utf8");
    assert.equal(src.includes("document"), false, name + " mentions document");
    assert.equal(src.includes("localStorage"), false, name + " mentions localStorage");
    assert.equal(src.includes("window."), false, name + " mentions window");
  }
});

test("AT3 SEO + audience: promote CPC 2x and conversion not improved", () => {
  const withSeo = createState(seoAudience);
  const noSeo = createState({ ...seoAudience, seo: false });
  assert.equal(promoteCpc(withSeo), promoteCpc(noSeo) * 2);
  assert.ok(getConversion(withSeo) < getConversion(noSeo), "SEO haircut must lower conversion");
});

test("AT4 paid search, audience off: traffic up, year profit <= 0", () => {
  const paid = createState(paidCold);
  const none = createState({ ...paidCold, paidSearch: false });
  assert.ok(getTraffic(paid) > getTraffic(none), "paid search must raise traffic");
  runYear(paid, createRng(1));
  assert.equal(paid.day, TOTAL_DAYS);
  assert.ok(communityShare(paid) <= 0, "cold paid search must not profit");
});
