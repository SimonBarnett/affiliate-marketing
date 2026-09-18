/** Named fixtures for ?scenario= */

export const SCENARIOS = {
  "cold-start": {
    partner: false, hasAudience: false, seo: false, contact: false, content: false,
    paidSearch: false, usp: false, reviews: false, intensity: 0, printDigital: "digital",
  },
  "print-hangover": {
    partner: false, hasAudience: false, seo: false, contact: false, content: false,
    paidSearch: false, usp: false, reviews: false, intensity: 0, printDigital: "print",
    untrackedSpend: 500,
  },
  "usp-off": {
    partner: true, hasAudience: true, seo: false, contact: true, content: true,
    paidSearch: false, usp: false, reviews: true, intensity: 30, printDigital: "digital",
  },
  "healthy": {
    partner: true, hasAudience: true, seo: false, contact: true, content: true,
    paidSearch: false, usp: true, reviews: true, intensity: 40, printDigital: "digital",
  },
  "portfolio": { _portfolio: true },
  "merchant-storm": { _platform: true, _storm: true },
};
