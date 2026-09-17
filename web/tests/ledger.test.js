import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createRng } from "../sim/rng.js";
import { createState, runYear } from "../sim/kernel.js";
import { debriefSentences, ledgerTotals } from "../sim/ledger.js";

const here = dirname(fileURLToPath(import.meta.url));
const load = (name) => JSON.parse(readFileSync(join(here, "fixtures", name), "utf8"));
const healthy = load("healthy.json");
const uspOff = load("usp-off.json");

test("AT6 full year ledger has 12 months and untrackedPrint + uspOffCommissionLost", () => {
  const st = createState(healthy);
  runYear(st, createRng(42));
  assert.equal(st.ledger.length, 12, "monthsPlayed");
  for (const row of st.ledger) {
    assert.equal("untrackedPrint" in row, true);
    assert.equal(typeof row.untrackedPrint, "number");
    assert.equal("uspOffCommissionLost" in row, true);
  }
  const t = ledgerTotals(st.ledger);
  assert.equal(t.monthsPlayed, 12);
  assert.equal(typeof t.uspOffCommissionLost, "number");
  assert.equal(t.untrackedPrint, 0);
  const lines = debriefSentences(st.ledger);
  assert.equal(lines.length, 3);
});

test("AT6 USP-off year records commission lost", () => {
  const st = createState(uspOff);
  runYear(st, createRng(7));
  const t = ledgerTotals(st.ledger);
  assert.ok(st.ledger.length === 12 || t.monthsPlayed >= 1);
  assert.ok(t.uspOffCommissionLost > 0, "audience + USP off must leak capture");
});
