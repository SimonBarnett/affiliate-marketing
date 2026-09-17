# Affiliate Marketing Simulator

Club Madeira training sim: configure traffic and conversion strategies, run a 12-month year, and see whether the partner programme pays.

This repo holds both implementations:

| Path | What it is |
|------|------------|
| `web/` | Canvas port. Hosted on AWS Amplify at **https://sim.ntsa.uk** |
| `desktop/` | Original pygame app (Windows `.exe` via PyInstaller) |

**Ship only to https://sim.ntsa.uk.** Do not change [partner.clubmadeira.io/sim.html](https://partner.clubmadeira.io/sim.html) or the S3 widget until an explicit cutover.

Agent handoff (AWS account, Amplify app id, DNS, CloudShell creds): [docs/handoff-aws.md](docs/handoff-aws.md). Economy dump: [docs/economy-from-source.md](docs/economy-from-source.md).

## Web

Open `web/index.html` locally, or serve the folder:

```powershell
cd web
python -m http.server 8080
```

Then visit `http://localhost:8080`. The game mounts with:

```js
AffiliateMarketing.mount(document.getElementById('am-game'));
```

High scores and last P&L live in `localStorage` (`am_highscores_v1`, `am_last_pnl_v1`). Month debrief is `am_last_ledger_v1`.

Year math is in `web/sim/` (no DOM). Tests (Node 20+):

```powershell
npm test
```

### Amplify

`amplify.yml` publishes `web/` as a static site. Custom domain: `sim.ntsa.uk` on `ntsa.uk` (Talk Internet DNS).

After a GitHub connect, Amplify needs:

1. A `CNAME` for `sim` → the Amplify CloudFront domain
2. Any ACM validation CNAMEs Amplify prints for the certificate

## Desktop

Python 3.10+, pygame.

```powershell
cd desktop
pip install -r requirements.txt
python affiliate_marketing.py
```

Windows exe:

```powershell
cd desktop
.\build_windows.bat
```

Output: `desktop/dist/AffiliateMarketing.exe`. Icon is `dial_icon.ico`; splash is `splash.png`.

## Layout

```
web/                        # Amplify artifact root
  index.html
  affiliate_marketing.js
  welcome_hero.jpg
  favicon.ico
desktop/
  affiliate_marketing.py
  requirements.txt
  build_windows.bat
  AffiliateMarketing.spec
  splash.png
  dial_icon.ico
amplify.yml
```

## Origins

- Desktop: `madeira/affiliate_marketing` (pygame)
- Web: canvas port previously served from `madeira-widget-bucket` and `HOST/partner/sim.html` in [SimonBarnett/AWS](https://github.com/SimonBarnett/AWS)
