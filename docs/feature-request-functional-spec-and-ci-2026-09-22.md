# Feature request: functional spec + CI (2026-09-22)

**Issue:** https://github.com/SimonBarnett/affiliate-marketing/issues/1  
**Repo:** https://github.com/SimonBarnett/affiliate-marketing  
**Review:** flamingo-17568 after Simon `#bobiverse` 2026-09-22 (`review this for a FR`).

## What the tree already is

Club Madeira partner-programme training sim.

| Path | Role |
|------|------|
| `web/` | Canvas port. Amplify publishes this folder. |
| `web/sim/` | DOM-free year kernel + economy + ledger + cards. |
| `desktop/` | Original pygame app. Do not rewrite it in the same PR as the web kernel. |
| `docs/economy-from-source.md` | Economy dump. Source (`web/sim` / `affiliate_marketing.js`) wins. |
| `docs/handoff-aws.md` | Agent AWS/Amplify notes. Do not copy secrets into new docs. |

Ship target already locked in README: **https://sim.ntsa.uk** only. Do not change partner.clubmadeira.io/sim.html or the S3 widget until an explicit cutover.

`npm test` runs `node --test web/tests` (kernel, ledger, club, platform, cards, portfolio). There is **no** `.github/workflows` CI. There is **no** `docs/functional-spec.md`. There are **no** GitHub issues.

Web UI already has three seats (`partner` / `club` / `platform`), merchants, co-op, chest cards, and writes month debrief to `am_last_ledger_v1` (`LS_LEDGER` in `web/sim/ledger.js`). README documents that key.

## Gap vs current tree

1. Agents have economy + AWS handoff but no LOCKED functional spec / acceptance IDs / phase order. Next Bob jobs will invent scope.
2. `docs/economy-from-source.md` still says `am_last_ledger_v1` is **not yet — WP1b**. That is stale; the key is live.
3. Tests are local-only. A PR can land without `npm test`.

## LOCKED

| ID | Requirement |
|----|-------------|
| AM-L1 | Park `docs/functional-spec.md` from this review (seats, ship URL, economy-from-source as numbers source, desktop split). |
| AM-L2 | Ship only to https://sim.ntsa.uk. Do not edit partner.clubmadeira.io or `madeira-widget-bucket` in this FR. |
| AM-L3 | Do not invent a second economy. Currency in the HUD is `$`. Kernel keeps daily `stepDay` (not 12 monthly ticks). |
| AM-L4 | Web kernel PRs must not rewrite `desktop/`. Desktop PRs must not rewrite `web/sim/`. |
| AM-L5 | Add CI that runs `npm test` on pull requests. Node 20+. |
| AM-L6 | Correct the stale `am_last_ledger_v1` / WP1b line in `docs/economy-from-source.md`. |
| AM-L7 | No secrets in git. Do not paste AWS keys, Amplify deploy secrets, or `password=` / `XAI_API_KEY=` assignments. |
| AM-L8 | Workers do not stamp ready for human UAT. Bob only. |

## UNKNOWN

| ID | Item |
|----|------|
| AM-U1 | Whether desktop pygame must ever grow club/platform seats (web already has them). |
| AM-U2 | Whether `web/sim.html` (duplicate of `index.html`) should stay. |
| AM-U3 | Design-UAT of live sim.ntsa.uk (spelling / pixel / brief nits) — later FR, not this ticket. |

## Out of this FR

Desktop rewrite. Partner-site cutover. New economy numbers. Campaign copy (`club-madeira-campaign`). Worker UAT stamp.

## Acceptance

| ID | Done when |
|----|-----------|
| AM-A1 | `docs/functional-spec.md` is on the PR and linked from README. |
| AM-A2 | `.github/workflows` runs `npm test` on PRs. |
| AM-A3 | Economy doc no longer claims `am_last_ledger_v1` is not yet. |
| AM-A4 | PR URL. Never push `main`. Never merge. |
