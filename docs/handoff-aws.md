# Handoff — sim.ntsa.uk (do not touch partner)

Paste this whole file to another build agent.

## What this is

Club Madeira affiliate marketing simulator. **Only ship to https://sim.ntsa.uk.**  
Do **not** change [partner.clubmadeira.io/sim.html](https://partner.clubmadeira.io/sim.html), `madeira-widget-bucket`, or `HOST/partner` in `SimonBarnett/AWS` until the sim is finished and someone explicitly cuts over.

## Git

- Repo (private): https://github.com/SimonBarnett/affiliate-marketing
- Branch: `main`
- Local clone on this machine: `C:\Users\Administrator\src\affiliate-marketing`
- Owner: `SimonBarnett`
- Amplify deploy key on the repo (leave it): `d1midq3x5hctnh:amplify@aws`

Web root is `web/` (`index.html`, `affiliate_marketing.js`). Desktop pygame is `desktop/` — do not rewrite it in the same PRs as the web kernel.

## AWS

- Account: `620257466932` (root / console user)
- Region: **eu-west-2**
- This Windows box does **not** keep long-lived IAM keys. CloudShell has the session.

Get credentials in AWS CloudShell (`~ $`):

```bash
aws sts get-caller-identity
aws configure export-credentials --format env
```

Expect `Arn: arn:aws:iam::620257466932:root`. Paste the three `export AWS_…` lines into the agent session (they expire in ~1 hour). Do not commit them.

## Amplify

| | |
|--|--|
| App name | `sim.ntsa.uk` |
| App id | `d1midq3x5hctnh` |
| Repo | `https://github.com/SimonBarnett/affiliate-marketing` |
| Branch | `main` (auto-build on) |
| Artifact | `web/` via `amplify.yml` |
| Default URL | https://main.d1midq3x5hctnh.amplifyapp.com |
| Custom domain | **https://sim.ntsa.uk** (associated as domain `sim.ntsa.uk`, empty prefix) |
| CloudFront | `di1uqfuy3y6e6.cloudfront.net` |

`ntsa.uk` is already on a **different** app (RPSGame `d2r1gt4l4gumjj` → `rps.ntsa.uk`). Do not steal that domain association. This sim uses hostname `sim.ntsa.uk` as its own Amplify domain.

Push to `main` should build. If not:

```bash
aws amplify start-job --region eu-west-2 --app-id d1midq3x5hctnh --branch-name main --job-type RELEASE
```

GitHub email about SSH key `d1midq3x5hctnh:amplify@aws` is expected. Do not delete it.

## DNS (Talk Internet)

Zone: `ntsa.uk` at https://dnsgate.talkinternet.co.uk/index.php  
Already added:

| Type | Host | Value |
|------|------|--------|
| CNAME | `sim` | `di1uqfuy3y6e6.cloudfront.net` |
| CNAME | `_0278d78c0385a1030cbd0b46e1f75558.sim.ntsa.uk.` | `_cf2efbf9f4c845f17e7147177cb2025b.wzccmgtwzk.acm-validations.aws.` |

ACM cert is issued for `sim.ntsa.uk` + `*.sim.ntsa.uk` (Amazon RSA 2048). If a browser still says Not secure, it is a cached cert error — Incognito.

LAN DNS `192.168.1.200` may NXDOMAIN while 8.8.8.8 / 1.1.1.1 resolve.

## Product law (from the build-plan PDF)

Repo copy of the spec: `P:\madeira\affiliate_marketing\Club_Madeira_Affiliate_Sim_Build_Plan.pdf`  
Work WP0 → WP3 web-first, stop and demo. Source economy lives in `web/affiliate_marketing.js` (daily tick, `$`). Dump: `docs/economy-from-source.md`. Source wins over PDF freeze numbers.

Healthy year = Partner live ∧ Audience ∧ Promote > 0 ∧ USP. Do not make print-only win.

## Do not

- Edit `SimonBarnett/AWS` `HOST/partner/sim.html`
- Upload JS to `s3://madeira-widget-bucket`
- Redeploy `partner.clubmadeira.io`
- Associate Amplify custom domain `ntsa.uk` (that is RPS)
- Commit AWS keys or GitHub tokens
