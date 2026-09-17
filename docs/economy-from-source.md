# Economy from source (WP0)

Extracted from `web/affiliate_marketing.js` on 2026-09-17. **Source wins** over PDF freeze numbers. Currency in the HUD is `$`. Do not invent a second economy.

## Tick

| Item | Source |
|------|--------|
| Game day | `S.day` integer 0 … `TOTAL_DAYS` |
| Real time | `1s ≈ 6 game days` (`S.dayTimer += dt * 6`) |
| Month lengths | `DAYS_PER_MONTH = [31,28,31,30,31,30,31,31,30,31,30,25]` (Dec is 25) |
| Year length | `TOTAL_DAYS` = sum = **365** |
| Month index | `dayToDate(d).mi` 0–11; `currentMonth()` is 1–12 |

PDF freeze said “1 tick = 1 month unless source is finer”. Source is **daily**. Kernel must keep `stepDay`. Do not collapse the live year to 12 monthly ticks.

## Constants

| Name | Value | Role |
|------|-------|------|
| `MONTHLY_COST` | 20 | Partner retainer, charged when `currentMonth() > lastMonthCharged` if `partner` |
| `ADSPEND_MONTHLY_CAP` | 200 | Promote+paid monthly cap **with** audience |
| `ADSPEND_HARD_CAP` | 1000 | Cap **without** audience; also paid-search remaining |
| `PAID_SEARCH_DAILY` | 6 | `$/game-day` if Paid search on; `×0.75` if partner |
| `CONTACT_ENGAGEMENT_BONUS` | 1.0 | Added to conversion “other” if contact ∧ audience |
| `CONTACT_TRAFFIC_BONUS` | 15 | Traffic strat if contact ∧ audience |
| `SEO_TRAFFIC_POINTS` | 18 | SEO traffic if **no** audience |
| `SEO_TRAFFIC_CLUB` | 3.5 | SEO traffic **with** audience |
| `SEO_CLUB_CONV_HAIRCUT` | 0.25 | Subtracted from conv if SEO ∧ audience (floor 0.5) |
| `CPC_BASE` | 0.75 | Promote CPC without audience |
| `AUDIENCE_CPC` | 0.15 | Promote CPC with audience |
| `VISITORS_PER_INTENSITY` | 0.5 | Promote visitors = intensity × this |
| `MIN_WORTH_IT` | 600 | Year 2+ net floor (`not_worth`) |
| `ACCEPTABLE_DECLINE` | 0.5 | Year N vs N−1 drop allowed before `worse_than_last` |
| `LOSS_PROMOTE_LIMIT` | -100 | Named in source; early stop uses `EARLY_CONTRACT_LOSS` |
| `EARLY_CONTRACT_LOSS` | -1000 | If `money < -1000` during run → `early_loss` |
| `MAX_HOLD` | 1.0 s | Promote hold cap |
| `COOLDOWN` | 3.0 s | After max hold |
| Product commission | 10–30% random | `commission_rate` |
| Club take | **0.25** of gross commission | `clubEarn = commission * 0.25` |
| Partner take (HUD) | **0.25** of gross | display only in P&amp;L |
| Platform take (HUD) | **0.50** of gross | display only in P&amp;L |

Partner **unlocks** audience, SEO, contact, content, reviews. No partner → `tryAutoSale` returns 0 (no sales).

## Conversion (`getConversion`)

```
base = 1.0
clubOn = USP tactic checked   // label "My club get the commission", bonus 1.0, mult
other = sum of non-mult checked tactics (Paid search 1.5, Product reviews 2.0)
        + CONTACT_ENGAGEMENT_BONUS if contact ∧ audience
conv = clubOn ? base + 1.0 + other * 2.0 : base + other
if seo ∧ audience: conv = max(0.5, conv - 0.25)
```

USP needs audience in the UI lock; capture uses USP separately.

## Traffic (`getTrafficPotential` / `getTraffic`)

Clamped 0–100.

**With audience:**  
`organic 25 + strat + promo + seoT + paidT`  
- content → strat +14  
- contact → strat +15  
- if partner: strat ×2, promo = intensity × 0.5  
- else promo = intensity × 0.35  
Then if audience ∧ !partner: subtract 12.5 (`getTraffic`).

**Without audience:**  
`promo + seoT + paidT` with promo = intensity × (partner ? 1.5 : 1.0)

SEO traffic: audience ? 3.5 : 18; if partner ∧ !audience ×1.25.  
Paid search: 14, ×1.15 if partner.

## Capture (`getCommissionCapture`)

| Condition | Capture |
|-----------|---------|
| USP on ∧ audience | 1.00 |
| audience, USP off | 0.65 |
| no audience | 0.90 |

## Sales (`tryAutoSale`) — per game day

Requires `partner` and products.  
`visitors = (traffic/100)*40`  
`expected = visitors * (conv/100)`  
`p = min(0.92, expected)`  
Bernoulli `Math.random() < p` → one product sale.  
`commission = price * rate * capture`  
Club cash `+= commission * 0.25`. Gross GMV `totalRevenue += price`.

## Daily costs (inside `tick` day loop)

**Paid search:** `daily = 6 * (partner ? 0.75 : 1)`, clipped by `ADSPEND_HARD_CAP - monthlyAdspend`.

**Promote** if intensity > 1:  
`spend = intensity * 0.5 * cpc`  
`cpc = (audience ? 0.15 : 0.75) * (partner ? 0.65 : 1) * ((seo ∨ paidSearch) ? 2 : 1)`  
clipped by monthly cap (200 with audience else 1000). Tiny floor 0.05 with audience.

**Month roll:** if `currentMonth() > lastMonthCharged`: charge `$20` if partner; reset `monthlyAdspend`.

## Year-end (`finalizeYearAccounts` / `snapshotPnl`)

Remaining days simulated at `avgPromo = 30` (not live intensity).  
Community share: `totalCommission * 0.25 - totalAdspend - partnerFees` (`communityShareNow`).  
Loss if net &lt; 0 (`loss`), or year≥2 net &lt; 600 (`not_worth`), or drop vs last year beyond 50% (`worse_than_last`).  
High scores: top 3 nets in `am_highscores_v1`. P&amp;L blob `am_last_pnl_v1` is **year totals**, not a month ledger.

## PDF freeze vs source

| PDF freeze | Source | Winner |
|------------|--------|--------|
| 1 tick = 1 month | 1 tick = 1 **day** | source |
| Partner $20/mo | $20 | same |
| 25% partner / 25% club / rest platform | 25 / 25 / 50 | same |
| USP +1pt, capture 65→100 | yes | same |
| SEO Promote ×2 + conv haircut | ×2 and −0.25 with audience | same |
| Trust, print trap, churn, chest | **not in source** | add in WP2–WP3; do not retcon year math |
| High-score blocked if print-only | **not in source** | add as `highScoreEligible` (AT10) |
| £ vs $ | HUD is `$` | `$` |

## Kernel wrap list (do not copy DOM)

`paidSearchOn`, `clubCommissionOn` (USP), `getConversion`, `getTrafficPotential`, `getTraffic`, `getCommissionCapture`, `tryAutoSale` (pure: return sale or null; view plays sound), daily paid-search charge, daily promote charge, month retainer, `finalizeYearAccounts`, `communityShareNow`, `snapshotPnl` (decision only), `recordHighScore` (eligibility later).  
View keeps: canvas, Promote hold/cooldown, products flash, audio, `S` animation fields.

## Storage keys

| Key | Contents |
|-----|----------|
| `am_highscores_v1` | top 3 `{net,sales,revenue,settings}` |
| `am_last_pnl_v1` | year P&amp;L |
| `am_last_ledger_v1` | **not yet** — WP1b |
