#!/usr/bin/env python3
"""
Affiliate Marketing Game
Configure strategies → Start → run 12 months (1 second = 6 days).
Sales auto-generate from traffic × conversion. Products flash on sale.
10–30% commission per product, Partner $20/mo opt-in costs. Monitor turns greener with profit, redder with loss.
"""

import pygame
import math
import sys
import random
import json
import os

# ---------------------------------------------------------------------------
# Early low-memory boot frame (shows ASAP while the rest of the game loads)
# Keeps the window responsive during slow PyInstaller / cold-start import.
# ---------------------------------------------------------------------------
pygame.display.init()
pygame.font.init()
WIDTH, HEIGHT = 1280, 820
is_fullscreen = True
try:
    display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
except Exception:
    is_fullscreen = False
    display = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Affiliate Marketing Game")
# Tiny surfaces only — no mixer, no large assets yet
_boot_font = pygame.font.SysFont("segoeui", 28, bold=True)
_boot_small = pygame.font.SysFont("segoeui", 16)
_BOOT_BG = (18, 20, 28)
_BOOT_ACCENT = (64, 160, 255)
_BOOT_GREEN = (50, 200, 110)

_boot_closed = False

def _boot_blit_to_display(surf):
    """Scale a logical surface onto the display with letterbox (same as present)."""
    dw, dh = display.get_size()
    display.fill(_BOOT_BG)  # full clear — no leftover edges in fullscreen
    scale = min(dw / WIDTH, dh / HEIGHT)
    nw, nh = max(1, int(WIDTH * scale)), max(1, int(HEIGHT * scale))
    scaled = pygame.transform.smoothscale(surf, (nw, nh))
    display.blit(scaled, ((dw - nw) // 2, (dh - nh) // 2))
    pygame.display.flip()
    pygame.event.pump()

def _boot_present(msg="Loading…", progress=0.0):
    """Lightweight loading frame on a logical canvas (no fullscreen edge ghosts)."""
    surf = pygame.Surface((WIDTH, HEIGHT))
    surf.fill(_BOOT_BG)
    # Subtle grid
    for x in range(0, WIDTH, 40):
        pygame.draw.line(surf, (32, 38, 52), (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, 40):
        pygame.draw.line(surf, (32, 38, 52), (0, y), (WIDTH, y), 1)
    card_w, card_h = 560, 200
    card = pygame.Rect(WIDTH // 2 - card_w // 2, HEIGHT // 2 - card_h // 2, card_w, card_h)
    pygame.draw.rect(surf, (28, 32, 44), card, border_radius=14)
    pygame.draw.rect(surf, _BOOT_ACCENT, card, 2, border_radius=14)
    title = _boot_font.render("Affiliate Marketing Simulator", True, (240, 242, 250))
    surf.blit(title, (WIDTH // 2 - title.get_width() // 2, card.y + 36))
    sub = _boot_small.render(msg, True, (160, 170, 190))
    surf.blit(sub, (WIDTH // 2 - sub.get_width() // 2, card.y + 90))
    bar = pygame.Rect(card.x + 50, card.y + 140, card_w - 100, 10)
    pygame.draw.rect(surf, (40, 44, 58), bar, border_radius=5)
    fill = max(0, min(1.0, progress))
    if fill > 0:
        pygame.draw.rect(surf, _BOOT_GREEN,
                         (bar.x, bar.y, int(bar.w * fill), bar.h), border_radius=5)
    _boot_blit_to_display(surf)

_boot_present("Starting…", 0.05)

def _close_boot_splash():
    """Hide native PyInstaller splash + wipe any boot pixels from the display."""
    global _boot_closed
    # Native splash (frozen exe only) — close more than once if needed
    for _ in range(3):
        try:
            import pyi_splash
            if pyi_splash.is_alive():
                pyi_splash.close()
        except Exception:
            break
    # Full-display clear so letterbox edges never keep boot/splash remnants
    try:
        display.fill(_BOOT_BG)
        pygame.display.flip()
        display.fill((22, 24, 32))
        pygame.display.flip()
    except Exception:
        pass
    _boot_closed = True

pygame.init()  # remaining pygame modules
_boot_present("Initialising display…", 0.15)

# Logical canvas (always 1280×820). Display may be larger in fullscreen.
canvas = pygame.Surface((WIDTH, HEIGHT))
screen = canvas  # all drawing targets the logical canvas
clock = pygame.time.Clock()
_boot_present("Preparing canvas…", 0.25)

def present():
    """Blit canvas to display with letterbox/pillarbox padding in fullscreen."""
    # Always wipe the whole display first so no splash/boot edges linger
    display.fill((22, 24, 32))
    if is_fullscreen:
        dw, dh = display.get_size()
        scale = min(dw / WIDTH, dh / HEIGHT)
        nw, nh = max(1, int(WIDTH * scale)), max(1, int(HEIGHT * scale))
        scaled = pygame.transform.smoothscale(canvas, (nw, nh))
        display.blit(scaled, ((dw - nw) // 2, (dh - nh) // 2))
    else:
        display.blit(canvas, (0, 0))
    pygame.display.flip()
    # Ensure native splash is gone once the game is presenting frames
    if not _boot_closed:
        _close_boot_splash()

def map_mouse(pos):
    """Map display mouse coords → logical canvas coords (fullscreen padding)."""
    if not is_fullscreen:
        return pos
    dw, dh = display.get_size()
    scale = min(dw / WIDTH, dh / HEIGHT)
    nw, nh = max(1, int(WIDTH * scale)), max(1, int(HEIGHT * scale))
    ox, oy = (dw - nw) // 2, (dh - nh) // 2
    mx, my = pos
    # Outside letterbox → clamp to edge
    lx = (mx - ox) / scale
    ly = (my - oy) / scale
    return (int(max(0, min(WIDTH - 1, lx))), int(max(0, min(HEIGHT - 1, ly))))

_boot_present("Loading audio…", 0.40)

# Soft sale chime (quiet sine blip — less annoying) — deferred after splash
sale_sound = None
audio_enabled = True
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    import array, math as _m
    sample_rate = 22050
    duration = 0.06
    frequency = 660  # softer mid tone
    n_samples = int(sample_rate * duration)
    buf = array.array("h")
    for i in range(n_samples):
        t = i / sample_rate
        env = (1.0 - t / duration) ** 1.5  # gentle decay
        # soft sine instead of harsh square
        val = int(4500 * env * _m.sin(2 * _m.pi * frequency * t))
        buf.append(max(-32767, min(32767, val)))
    sale_sound = pygame.mixer.Sound(buffer=buf)
    sale_sound.set_volume(0.25)
except Exception:
    sale_sound = None

_boot_present("Loading game data…", 0.55)

# Colors
BG = (22, 24, 32)
BEZEL = (45, 48, 58)
MONITOR_INNER = (18, 20, 28)
BROWSER_BG = (32, 36, 48)
BROWSER_HEADER = (40, 44, 58)
CARD_BG = (48, 52, 68)
ACCENT_BLUE = (64, 160, 255)
ACCENT_GREEN = (50, 220, 120)
ACCENT_ORANGE = (255, 160, 60)
WHITE = (240, 242, 250)
GRAY = (160, 165, 180)
DARK_GRAY = (70, 75, 90)
BLACK = (0, 0, 0)
GLOW_GREEN = (80, 255, 160)
RED = (220, 70, 70)
PANEL_BG = (28, 30, 42)
COLUMN_BG = (34, 36, 50)
DISABLED = (90, 90, 100)
TOOLTIP_BG = (15, 18, 28)
TOOLTIP_BORDER = (80, 140, 220)

# ---------------------------------------------------------------------------
# Conversion strategies
# ---------------------------------------------------------------------------
conversion_strategies = [
    {
        "label": "Paid search",
        "bonus": 1.5,
        "is_multiplier": False,
        "checked": False,
        "help": "What: always-on Google Ads (~$6/day) that buy qualified commercial clicks. "
                "Effect: adds external traffic volume and raises conversion (searchers already intend to buy). "
                "Money: paid to Google — never to the partner. Available with or without an audience. "
                "Club members are already interested by definition; paid search still adds non-member volume. "
                "Side effect: Promote costs 2× while this is on. "
                "Source: https://www.affiliatebooster.com/affiliate-conversion-rates-by-traffic-source/"
    },
    {
        "label": "Product reviews",
        "bonus": 2.0,
        "is_multiplier": False,
        "checked": False,
        "help": "What: trusted product reviews on the catalogue (partner-supported). "
                "Needs: Partner Promotion — communities will not produce reviews without support. "
                "Effect: social proof lifts conversion (commonly 10–30% relative in retail studies). "
                "Source: https://ecomhint.com/blog/ecommerce-conversion-rate-benchmarks-by-industry"
    },
    {
        "label": "My club get the commission",
        "bonus": 1.0,
        "is_multiplier": True,
        "checked": False,
        "help": "What: Smart Catalogue USP — JS embed on the club site so members buy where THEIR club earns the commission. "
                "Needs: Has an Audience. "
                "Effect: +1% conversion; other conversion tactics become ~2× as effective; commission capture rises from ~65% to 100% "
                "(members stop leaking purchases to Amazon). They choose the club on purpose. "
                "Source: Smart Catalogue club-benefit model."
    },

]
# Traffic strategies
has_audience = False
seo_checked = False
content_updates = False
regular_contact = False
partner_promo = False  # opt-in consultancy; off at start — without it, 50% of members don't visit
club_site_url = None  # set when partner is selected — their customer club website

CLUB_TOWNS = [
    "bristol", "leeds", "exeter", "norwich", "york", "bath", "chester", "durham",
    "oxford", "cambridge", "brighton", "plymouth", "swansea", "cardiff", "glasgow",
    "edinburgh", "belfast", "coventry", "sheffield", "nottingham", "reading", "luton",
]
CLUB_SPORTS = [
    "rugby", "cricket", "football", "hockey", "tennis", "netball", "rowing",
    "athletics", "squash", "cycling", "golf", "sailing", "bowls", "triathlon",
]

def pick_club_site_url():
    """Partner recommends their customer — a real club site to host the catalogue."""
    town = random.choice(CLUB_TOWNS)
    sport = random.choice(CLUB_SPORTS)
    return f"{town}{sport}club.com"

last_month_charged = 0
def _persistent_data_dir():
    """Folder for highscores / last P&L that survives between runs.

    - Frozen exe (PyInstaller): next to the .exe (not the temp _MEIPASS unpack dir).
      If that folder is not writable (e.g. Program Files), fall back to AppData.
    - Source run: next to this script.
    """
    if getattr(sys, "frozen", False):
        # sys.executable is the .exe path when frozen
        candidates = [os.path.dirname(os.path.abspath(sys.executable))]
        # Windows user data fallback
        appdata = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if appdata:
            candidates.append(os.path.join(appdata, "AffiliateMarketing"))
        # Unix fallback
        home = os.path.expanduser("~")
        if home and home != "~":
            candidates.append(os.path.join(home, ".affiliate_marketing"))
    else:
        candidates = [os.path.dirname(os.path.abspath(__file__))]

    for folder in candidates:
        try:
            os.makedirs(folder, exist_ok=True)
            probe = os.path.join(folder, ".write_test")
            with open(probe, "w") as f:
                f.write("ok")
            os.remove(probe)
            return folder
        except Exception:
            continue
    # Last resort: cwd
    return os.getcwd()

_DATA_DIR = _persistent_data_dir()
HIGHSCORE_PATH = os.path.join(_DATA_DIR, "highscores.json")
LAST_PNL_PATH = os.path.join(_DATA_DIR, "last_pnl.json")

high_scores = []  # list of {net, sales, settings}
_hs_click_rects = []  # filled by draw_game_over
_gameover_btn_rect = None  # CONTINUE / CATALOGUE LOST hit box
_gameover_show_lost = False  # True when button is CATALOGUE LOST
scores_recorded_for_run = False
last_gameover_available = False  # True after a finished year or saved last_pnl/highscores
flag_anim_t = 0.0
last_pnl = None  # snapshot of last year-end figures for flag reopen
viewing_historical_pnl = False  # True when reopening via flag (not end of this run)
just_finished_loss = False  # True when THIS year triggers Catalogue Lost
years_completed = 0  # how many years finished this career
last_year_net = None  # community net from previous year
MIN_WORTH_IT = 600.0  # after year 1, under this → not worth it
ACCEPTABLE_DECLINE = 0.50  # community tolerates up to 50% YoY decline


# Core state
intensity = 0.0
is_holding = False
promote_lock = False
max_hold_timer = 0.0
hold_duration = 0.0  # continuous hold time; max 1.0s then 3s cooldown
promote_cooldown = 0.0  # seconds remaining before promote can be used again
monthly_adspend = 0.0  # tracks AdSpend this month (for $50 cap with audience)
hover_help = None

# Game state
STATE_WELCOME = "welcome"
STATE_SETUP = "setup"
STATE_RUNNING = "running"
STATE_GAMEOVER = "gameover"
STATE_OUTRO = "outro"
game_state = STATE_WELCOME
welcome_timer = 0.0
outro_timer = 0.0
WELCOME_DURATION = 6.0  # seconds
OUTRO_DURATION = 5.0  # shutdown sequence
hud_anim_t = 0.0          # entrance progress 0→1
hud_pulse = 0.0           # balance change pulse
hud_display_money = 0.0   # smoothed balance for display
hud_prev_money = 0.0
hud_sale_flash = 0.0      # border flash on sale


day = 0                    # 0..359  (12 months × 30 days)
money = 0.0                # running balance
total_revenue = 0.0
total_commission = 0.0
total_costs = 0.0
total_adspend = 0.0
total_promote_adspend = 0.0  # to partner only when engaging own audience
total_paidsearch_adspend = 0.0  # always-on paid search burn
monthly_adspend = 0.0
sales_count = 0
last_sale_msg = ""
last_sale_timer = 0.0
flash_product_idx = -1
flash_timer = 0.0
sale_anims = []  # list of {x,y,t,life,text,vy}
MONTHLY_COST = 20.0
# Industry-standard paid traffic (blended CPC for ecommerce/affiliate cold traffic ~$0.70–$1.10)
# Modelled so full promote ≈ 50 visitors/day × $0.75 CPC ≈ $37.50/day
# SEO improves efficiency (~25% lower effective CPC); content quality also helps
ADSPEND_MONTHLY_CAP = 200.0  # soft cap when engaging own audience (cheap materials, not free)
ADSPEND_HARD_CAP = 1000.0    # hard monthly limit regardless of audience (anti-spam)
# Always-on Google/paid-search campaign burn (modest SMB-scale ~$5–10/day)
PAID_SEARCH_DAILY = 6.0
CONTACT_ENGAGEMENT_BONUS = 1.0
CONTACT_TRAFFIC_BONUS = 15.0
SEO_TRAFFIC_POINTS = 18.0  # ~RepublishAI +8 rank positions modelled as organic dial points
CPC_BASE = 0.75          # $ per paid visitor (industry blended average)
VISITORS_PER_INTENSITY = 0.50  # intensity 100 → 50 visitors/game-day
# With audience: promote is much more effective + cheaper, but capped $50/month
AUDIENCE_CPC = 0.15            # cheap promo materials to engage existing members (NOT free)
AUDIENCE_VISITORS_MULT = 3.5   # far more traffic per intensity point
AUDIENCE_MONTHLY_AD_CAP = 50.0
COMMISSION_RATE = 0.20  # fallback mid-range; each product has its own 10–30%
DAYS_PER_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 25]  # Jan–Nov full, Dec to 25th
TOTAL_DAYS = sum(DAYS_PER_MONTH)  # 359
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Product pools for randomisation
NAME_POOL = [
    "Wireless Earbuds Pro", "Smart Fitness Watch", "Ergo Laptop Stand",
    "USB-C Multiport Hub", "Mechanical Keyboard", "ANC Headphones",
    "Portable Power Bank", "RGB Desk Lamp", "Noise-Cancel Mic",
    "4K Webcam", "Travel Backpack", "Smart Water Bottle",
    "Wireless Charger Pad", "Bluetooth Speaker", "Gaming Mouse",
    "Standing Desk Mat", "Cable Management Kit", "Monitor Light Bar",
    "Folding Phone Stand", "UV Phone Sanitizer", "Mini Projector",
    "Smart LED Strip", "Ergo Foot Rest", "Laptop Cooling Pad",
    "Wireless Presenter", "Portable SSD 1TB", "Noise Machine",
    "Desk Organizer Set", "Magnetic Cable Pack", "Webcam Ring Light",
    "Travel Neck Pillow", "Insulated Tumbler", "Yoga Mat Roll",
    "Resistance Band Kit", "Foam Roller", "Grip Strengthener",
]
PRICE_POOL = [4.99, 7.99, 9.99, 12.99, 14.99, 19.99, 24.99, 29.99, 34.99,
              39.99, 44.99, 49.99, 54.99, 59.99, 69.99, 79.99, 89.99, 99.99]
COLOR_POOL = [
    (90, 140, 255), (255, 110, 80), (70, 200, 130), (190, 100, 220),
    (255, 190, 50), (80, 210, 210), (255, 140, 180), (140, 200, 80),
]

products = []

def randomise_products():
    global products
    chosen = random.sample(NAME_POOL, 6)
    products = []
    for name in chosen:
        products.append({
            "name": name,
            "price": random.choice(PRICE_POOL),
            "color": random.choice(COLOR_POOL),
            # Random affiliate commission 10–30%
            "commission_rate": random.randint(10, 30) / 100.0,
        })


def snapshot_settings():
    return {
        "has_audience": has_audience,
        "seo_checked": seo_checked,
        "content_updates": content_updates,
        "regular_contact": regular_contact,
        "partner_promo": partner_promo,
        "club_site_url": club_site_url,
        "conversion": {s["label"]: s["checked"] for s in conversion_strategies},
    }

def apply_settings(s):
    global has_audience, seo_checked, content_updates, regular_contact, partner_promo, club_site_url
    if not s:
        return
    has_audience = bool(s.get("has_audience", False))
    seo_checked = bool(s.get("seo_checked", False))
    content_updates = bool(s.get("content_updates", False))
    regular_contact = bool(s.get("regular_contact", False))
    partner_promo = bool(s.get("partner_promo", False))
    club_site_url = s.get("club_site_url") or (pick_club_site_url() if partner_promo else None)
    if not partner_promo:
        club_site_url = None
    conv_map = s.get("conversion", {})
    for strat in conversion_strategies:
        if strat["label"] in conv_map:
            strat["checked"] = bool(conv_map[strat["label"]])
    # Enforce gates
    if not has_audience:
        regular_contact = False
        content_updates = False
        for strat in conversion_strategies:
            if strat.get("is_multiplier") or False:
                strat["checked"] = False
    if not partner_promo:
        has_audience = False
        regular_contact = False
        seo_checked = False
        for strat in conversion_strategies:
            if strat["label"] == "Product reviews":
                strat["checked"] = False
            if False:
                strat["checked"] = False
            if strat.get("is_multiplier"):
                strat["checked"] = False
    if not regular_contact:
        for strat in conversion_strategies:
            if False:
                strat["checked"] = False

def load_high_scores():
    global high_scores, last_gameover_available
    try:
        if os.path.isfile(HIGHSCORE_PATH):
            with open(HIGHSCORE_PATH, "r") as f:
                data = json.load(f)
            if isinstance(data, list):
                high_scores = data[:3]
                if high_scores:
                    last_gameover_available = True
    except Exception:
        high_scores = []

def save_high_scores():
    try:
        with open(HIGHSCORE_PATH, "w") as f:
            json.dump(high_scores[:3], f)
    except Exception:
        pass

def snapshot_pnl(force_reason=None):
    """Store year-end figures and decide Catalogue Lost conditions.

    Lost if:
      - Community net < 0, or
      - Loss exceeds $1,000 mid-year (early contract end), or
      - After the first year: net < $600 (not worth it), or
      - After the first year: community share falls more than 50% vs last year.

    A decline of up to 50% is tolerated, but the community notes disappointment.
    """
    global last_pnl, last_gameover_available, just_finished_loss, viewing_historical_pnl
    global years_completed, last_year_net, money
    # Always judge the career on the community share (not gross commission)
    money = community_share_now()
    net = float(money)
    last_pnl = {
        "money": net,
        "sales_count": int(sales_count),
        "total_revenue": float(total_revenue),
        "total_commission": float(total_commission),
        "total_adspend": float(total_adspend),
        "total_promote_adspend": float(total_promote_adspend),
        "total_paidsearch_adspend": float(total_paidsearch_adspend),
        "total_costs": float(total_costs),
        "years_completed": years_completed,
        "last_year_net": last_year_net,
    }
    last_gameover_available = True
    viewing_historical_pnl = False
    disappointment = False
    if force_reason:
        lost = True
        loss_reason = force_reason
    else:
        # Communities only quit for: under $600 in a year, or >50% drop vs last year
        lost = False
        loss_reason = None
        if net < MIN_WORTH_IT:
            lost = True
            loss_reason = "not_worth"
        if years_completed >= 1 and last_year_net is not None:
            prev = float(last_year_net)
            if prev > 0 and net < prev:
                floor = prev * (1.0 - ACCEPTABLE_DECLINE)
                if net < floor:
                    lost = True
                    loss_reason = "worse_than_last"
                elif not lost:
                    disappointment = True
            elif prev <= 0 and net < prev:
                lost = True
                loss_reason = "worse_than_last"
    just_finished_loss = lost
    last_pnl["loss_reason"] = loss_reason
    last_pnl["disappointment"] = disappointment
    # Keep prior year net for the explanation message before advancing
    last_pnl["compared_to_year"] = float(last_year_net) if last_year_net is not None else None

    # Advance career counters for next year
    last_year_net = net
    years_completed += 1
    last_pnl["years_completed"] = years_completed
    last_pnl["last_year_net"] = last_year_net

    try:
        with open(LAST_PNL_PATH, "w") as f:
            json.dump(last_pnl, f)
    except Exception:
        pass

def restore_pnl(historical=True):
    """Reload last year-end figures into live counters for draw_game_over."""
    global money, sales_count, total_revenue, total_commission, total_adspend, total_costs
    global viewing_historical_pnl, just_finished_loss
    if not last_pnl:
        return
    money = float(last_pnl.get("money", 0))
    sales_count = int(last_pnl.get("sales_count", 0))
    total_revenue = float(last_pnl.get("total_revenue", 0))
    total_commission = float(last_pnl.get("total_commission", 0))
    total_adspend = float(last_pnl.get("total_adspend", 0))
    total_promote_adspend = float(last_pnl.get("total_promote_adspend", 0))
    total_paidsearch_adspend = float(last_pnl.get("total_paidsearch_adspend", 0))
    total_costs = float(last_pnl.get("total_costs", 0))
    if historical:
        viewing_historical_pnl = True
        just_finished_loss = False  # reopening past results is never a "this go" loss

def load_last_pnl():
    """Load last P&L from disk; show flag if file or highscores exist."""
    global last_pnl, last_gameover_available
    try:
        if os.path.isfile(LAST_PNL_PATH):
            with open(LAST_PNL_PATH, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                last_pnl = data
                last_gameover_available = True
                return
    except Exception:
        pass
    # Fallback: highscores file means a prior run existed
    try:
        if os.path.isfile(HIGHSCORE_PATH):
            last_gameover_available = True
            # Seed last_pnl from best score if we have no dedicated snapshot
            if high_scores and last_pnl is None:
                top = high_scores[0]
                last_pnl = {
                    "money": float(top.get("net", 0)),
                    "sales_count": int(top.get("sales", 0)),
                    "total_revenue": float(top.get("revenue", 0)),
                    "total_commission": float(top.get("net", 0)),  # approx
                    "total_adspend": 0.0,
                    "total_costs": 0.0,
                }
    except Exception:
        pass

def record_high_score():
    """If this run beats or fills the top 3, insert it and shift lower scores down.
    Sales count is the finalized P&L total for THIS run only (frozen copy).
    """
    global high_scores, scores_recorded_for_run
    if scores_recorded_for_run:
        return
    scores_recorded_for_run = True
    # Freeze values now so later runs cannot mutate this entry
    entry = {
        "net": float(community_share_now()),  # community share only
        "sales": int(sales_count),
        "revenue": float(total_revenue),
        "settings": snapshot_settings(),
        "is_current": True,
    }
    # Clear previous current flags on older scores
    combined = []
    for e in high_scores:
        e2 = dict(e)
        e2["is_current"] = False
        combined.append(e2)
    combined.append(entry)
    combined.sort(key=lambda e: float(e.get("net", 0)), reverse=True)
    high_scores = combined[:3]
    save_high_scores()

load_high_scores()
load_last_pnl()
try:
    _boot_present("Almost ready…", 0.85)
except Exception:
    pass

def reset_strategies():
    """Clear all strategy tickboxes to defaults (fresh career / after welcome)."""
    global has_audience, seo_checked, content_updates, regular_contact, partner_promo, club_site_url
    has_audience = False
    seo_checked = False
    content_updates = False
    regular_contact = False
    partner_promo = False
    club_site_url = None
    for s in conversion_strategies:
        s["checked"] = False

def reset_game(keep_strategies=True):
    """Start a new year.
    keep_strategies=True  → CONTINUE into next year (or load setup from high score)
    keep_strategies=False → full wipe (used after welcome / catalogue lost)
    """
    global intensity, is_holding, game_state, day, money
    global total_revenue, total_commission, total_costs, total_adspend, total_promote_adspend, total_paidsearch_adspend, sales_count
    global last_sale_msg, last_sale_timer, flash_product_idx, flash_timer
    global promote_lock, max_hold_timer, monthly_adspend, hold_duration, promote_cooldown
    global sale_anims
    if not keep_strategies:
        reset_strategies()
    intensity = 0.0
    is_holding = False
    promote_lock = False
    max_hold_timer = 0.0
    hold_duration = 0.0
    promote_cooldown = 0.0
    monthly_adspend = 0.0
    game_state = STATE_SETUP  # skip welcome on subsequent games
    day = 0
    money = 0.0
    total_revenue = 0.0
    total_commission = 0.0
    total_costs = 0.0
    total_adspend = 0.0
    total_promote_adspend = 0.0
    total_paidsearch_adspend = 0.0
    monthly_adspend = 0.0
    sales_count = 0
    last_sale_msg = ""
    last_sale_timer = 0.0
    flash_product_idx = -1
    flash_timer = 0.0
    sale_anims = []
    scores_recorded_for_run = False
    randomise_products()

randomise_products()

def fmt_money(n, signed=False):
    """Format currency with thousands separators."""
    n = float(n)
    if signed:
        return f"${n:+,.0f}"
    return f"${n:,.0f}"

def get_font(size, bold=False):
    try:
        return pygame.font.SysFont("DejaVu Sans", size, bold=bold)
    except Exception:
        return pygame.font.SysFont(None, size, bold=bold)

font_tiny = get_font(13)
font_small = get_font(15)
font_med = get_font(18)
font_med_bold = get_font(18, bold=True)
font_large = get_font(22, bold=True)
font_title = get_font(30, bold=True)
font_header = get_font(20, bold=True)
font_huge = get_font(36, bold=True)

# Layout
MONITOR_RECT = pygame.Rect(30, 50, 620, 520)
BROWSER_RECT = pygame.Rect(45, 80, 590, 470)
RIGHT_PANEL = pygame.Rect(680, 25, 570, 620)
TRAFFIC_COL = pygame.Rect(690, 40, 270, 590)
CONV_COL = pygame.Rect(970, 40, 270, 590)
PROMOTE_RECT = pygame.Rect(710, 430, 230, 48)
START_RECT = pygame.Rect(990, 430, 230, 48)
QUIT_RECT = pygame.Rect(990, 430, 230, 48)  # same slot during RUNNING
# Randomise products button — bottom of the monitor stand area
RANDOMISE_RECT = pygame.Rect(MONITOR_RECT.centerx - 90, MONITOR_RECT.bottom - 34, 180, 28)
AUDIO_RECT = pygame.Rect(MONITOR_RECT.right - 52, MONITOR_RECT.bottom - 52, 40, 40)
FLAG_RECT = pygame.Rect(MONITOR_RECT.right - 64, MONITOR_RECT.y + 6, 52, 36)

# Shared vertical alignment for traffic (left) and conversion (right) strategies
STRATEGY_START_Y = 245
STRATEGY_ROW_H = 34
PARTNER_Y = STRATEGY_START_Y          # row 0 — required for catalogue on site
AUDIENCE_Y = STRATEGY_START_Y + STRATEGY_ROW_H     # row 1
SEO_Y = STRATEGY_START_Y + 2 * STRATEGY_ROW_H      # row 2
CONTACT_Y = STRATEGY_START_Y + 3 * STRATEGY_ROW_H  # row 3
CONTENT_Y = STRATEGY_START_Y + 4 * STRATEGY_ROW_H  # row 4
CONV_START_Y = STRATEGY_START_Y        # conversion rows align with traffic
CHECK_H = STRATEGY_ROW_H
CHECK_SIZE = 20

TRAFFIC_KNOB = (825, 130)
CONV_KNOB = (1105, 130)
KNOB_R = 55
EQUATION_Y = 640

TRAFFIC_HELP = {
    "audience": "What: marks that the club has natural traffic — modelled as ~2k clicks/month minimum on the dial. "
                "Needs: Partner Promotion (only the partner can confirm an unmonetised engaged audience). "
                "Why it matters: without natural traffic you must buy clicks; AdSpend then makes affiliate marketing loss-making. "
                "Without partner support ~50% of members never visit (communities do not know how to engage them). "
                "SEO and Paid search stay available. "
                "Source: https://www.luckyorange.com/blog/posts/good-conversion-rate",
    "seo": "What: earns organic search visitors without paying per click. "
           "Needs: Partner Promotion — communities cannot run SEO alone. "
           "Evidence: RepublishAI (15k URLs) found substantial content expansion gains ~+8 ranking positions vs untouched pages (p=0.026). "
           "In this model that is a steady organic traffic lift on the dial. "
           "Audience = people you already know; SEO = strangers from search. "
           "Side effect: Promote costs 2× while SEO is on. "
           "Source: https://republishai.com/content-optimization/content-refresh/",
    "content": "What: fresh club content so existing members come back. "
               "Needs: Has an Audience (locked otherwise). "
               "Why: only members return for club posts (agenda, news). "
               "SEO visitors arrived via a product/search link — they will not return for club content. "
               "Source: https://www.workshopdigital.com/blog/content-refresh-analysis/",
    "partner": "What: the partner is a digital agency with club customers. When you enable this, they recommend one of their clubs "
                "(a random {town}{sport}club.com site) and log in to put the Smart Catalogue embed on that club's page. "
                "Needs: none — this unlocks audience, SEO, contact, and reviews. "
                "Why: you do not have a website of your own; without a partner there is nowhere to host the catalogue. "
                "Cost: $20/mo retained advice (steering + follow-ups). Partner also earns 25% of gross commission. "
                "Without partner support ~50% of members are not engaged; communities cannot do SEO, templates, or reviews alone. "
                "Money: promote to partner only when engaging own members; paid search always to Google.",
    "contact": "What: regular outreach to members (email/SMS/in-app) using partner-supplied templates. "
               "Needs: Partner Promotion and Has an Audience. "
               "Effect: boosts TRAFFIC (return visits) and CONVERSION (engaged members buy more). "
               "Turn it off and both lifts disappear. Engaging people you already have is far cheaper than buying new audience. "
               "Source: https://rule1.ai/articles/facebook-ads-benchmarks",
}

def get_conversion():
    """Baseline 1% is affiliate-marketing (not ecommerce) zero.
    Regular Contact adds engagement conversion lift (no separate tickbox).
    Club commission doubles other conversion bonuses.
    """
    base = 1.0
    other = 0.0
    club_bonus = 0.0
    club_on = False
    for s in conversion_strategies:
        if s.get("is_multiplier"):
            club_on = s["checked"]
            if club_on:
                club_bonus = s.get("bonus", 1.0)
        else:
            if s["checked"]:
                other += s["bonus"]
    if regular_contact and has_audience:
        other += CONTACT_ENGAGEMENT_BONUS
    if club_on:
        return base + club_bonus + other * 2.0
    return base + other


def community_share_now():
    """Community result only: 25% of gross commission − AdSpend − partner fee."""
    partner_fee = max(0.0, total_costs - total_adspend)
    return total_commission * 0.25 - total_adspend - partner_fee

def finalize_year_accounts():
    """Full-year P&L: keep real YTD results, project only the remaining days.

    Sales on the board = actual sales so far + estimated sales for days not yet played.
    High scores store that combined total for the run.
    """
    global money, total_costs, total_adspend, total_revenue, total_commission
    global total_promote_adspend, total_paidsearch_adspend
    global sales_count, last_month_charged, monthly_adspend, day, products

    if not products:
        randomise_products()

    # Snapshot what was already earned in play
    ytd_sales = int(sales_count)
    ytd_revenue = float(total_revenue)
    ytd_commission = float(total_commission)
    ytd_adspend = float(total_adspend)
    ytd_costs = float(total_costs)
    ytd_money = float(money)
    days_done = max(0, min(int(day), TOTAL_DAYS))
    remaining = max(0, TOTAL_DAYS - days_done)

    # Project remaining days only (not a full wipe of the year)
    avg_promote_intensity = 30.0
    traffic = _traffic_with_intensity(avg_promote_intensity) if partner_promo else 0.0
    conv = max(0.5, get_conversion()) if partner_promo else 0.0
    visitors_per_day = (traffic / 100.0) * 40.0
    expected_per_day = visitors_per_day * (conv / 100.0)
    # Slight run variance so two runs with the same setup are not identical
    n_remaining = max(0, int(round(expected_per_day * remaining * random.uniform(0.92, 1.08))))

    extra_revenue = 0.0
    extra_commission = 0.0
    extra_sales = 0
    for _s in range(n_remaining):
        prod = random.choice(products)
        rate = prod.get("commission_rate", COMMISSION_RATE)
        capture = get_commission_capture()
        commission = prod["price"] * rate * capture
        extra_commission += commission
        extra_revenue += prod["price"]
        extra_sales += 1

    # Remaining promote AdSpend estimate
    promote_days = remaining * 0.35
    visitors = avg_promote_intensity * VISITORS_PER_INTENSITY
    if has_audience:
        cpc = AUDIENCE_CPC * (0.65 if partner_promo else 1.0)
        monthly_cap = ADSPEND_MONTHLY_CAP
    else:
        cpc = CPC_BASE * (0.65 if partner_promo else 1.0)
        monthly_cap = ADSPEND_HARD_CAP
    months_left = max(1, 12 - last_month_charged)
    paid_search_on = any(s["label"] == "Paid search" and s["checked"] for s in conversion_strategies)
    if seo_checked or paid_search_on:
        cpc *= 2.0  # promote costs 2x with SEO / paid links
    promote_rest = min(visitors * cpc * promote_days, monthly_cap * months_left)

    # Remaining paid search
    ps_rest = 0.0
    if paid_search_on and remaining > 0:
        daily = PAID_SEARCH_DAILY * (0.75 if partner_promo else 1.0)
        ps_rest = min(daily * remaining, ADSPEND_HARD_CAP * months_left)

    # Remaining partner months
    partner_rest = 0.0
    months_to_bill = max(0, 12 - last_month_charged)
    if partner_promo and months_to_bill > 0:
        partner_rest = MONTHLY_COST * months_to_bill

    # Combine YTD + projection
    sales_count = ytd_sales + extra_sales
    total_revenue = ytd_revenue + extra_revenue
    total_commission = ytd_commission + extra_commission
    total_adspend = ytd_adspend + promote_rest + ps_rest
    # Promote is external; paid search may route via partner — keep split for P&L
    total_promote_adspend = max(0.0, float(total_promote_adspend) + promote_rest)
    total_paidsearch_adspend = max(0.0, float(total_paidsearch_adspend) + ps_rest)
    total_costs = ytd_costs + promote_rest + ps_rest + partner_rest
    money = ytd_money + extra_commission * 0.25 - promote_rest - ps_rest - partner_rest

    # If year never really started (quit day 0), fall back to full-year estimate
    if days_done == 0 and ytd_sales == 0:
        sales_count = 0
        total_revenue = 0.0
        total_commission = 0.0
        total_adspend = 0.0
        total_costs = 0.0
        money = 0.0
        n_full = max(0, int(round(expected_per_day * TOTAL_DAYS * random.uniform(0.92, 1.08))))
        for _s in range(n_full):
            prod = random.choice(products)
            rate = prod.get("commission_rate", COMMISSION_RATE)
            capture = get_commission_capture()
            commission = prod["price"] * rate * capture
            total_revenue += prod["price"]
            total_commission += commission
            money += commission * 0.25  # community share only
            sales_count += 1
        promote_year = min(visitors * cpc * (TOTAL_DAYS * 0.35),
                           (ADSPEND_MONTHLY_CAP if has_audience else ADSPEND_HARD_CAP) * 12)
        if seo_checked or paid_search_on:
            promote_year *= 2.0  # promote costs 2x with SEO / paid links
        money -= promote_year
        total_adspend += promote_year
        total_promote_adspend += promote_year
        total_costs += promote_year
        if paid_search_on:
            daily = PAID_SEARCH_DAILY * (0.75 if partner_promo else 1.0)
            ps_total = min(daily * TOTAL_DAYS, ADSPEND_HARD_CAP * 12)
            money -= ps_total
            total_adspend += ps_total
            total_paidsearch_adspend += ps_total
            total_costs += ps_total
        if partner_promo:
            fee = MONTHLY_COST * 12
            money -= fee
            total_costs += fee

    last_month_charged = 12
    day = TOTAL_DAYS
    monthly_adspend = 0.0


def _traffic_with_intensity(sim_intensity):
    seo_traffic = SEO_TRAFFIC_POINTS if seo_checked else 0.0
    if seo_checked and partner_promo:
        seo_traffic *= 1.25
    paid_traffic = 14.0 if _paid_search_on() else 0.0
    if _paid_search_on() and partner_promo:
        paid_traffic *= 1.15
    if has_audience:
        organic = 25.0
        strat = 0.0
        if content_updates:
            strat += 14.0
        if regular_contact:
            strat += CONTACT_TRAFFIC_BONUS
        if partner_promo:
            strat *= 2.0
            promo = sim_intensity * 0.50
        else:
            promo = sim_intensity * 0.35
        base = organic + strat + promo + seo_traffic + paid_traffic
        if not partner_promo:
            base = max(0.0, base - 12.5)
    else:
        promo = sim_intensity * (1.5 if partner_promo else 1.0)
        base = promo + seo_traffic + paid_traffic
    return max(0.0, min(100.0, base))


def _paid_search_on():
    return any(s["label"] == "Paid search" and s["checked"] for s in conversion_strategies)

def get_traffic_potential():
    """Traffic 0-100. Audience floor ~2k clicks/mo onboarding minimum (dial 25).
    SEO organic from ranking-lift evidence (RepublishAI ~+8 positions, p=0.026).
    Paid search always-on qualified volume. Regular Contact = cheap member engagement.
    """
    seo_traffic = SEO_TRAFFIC_POINTS if seo_checked else 0.0
    if seo_checked and partner_promo:
        seo_traffic *= 1.25
    paid_traffic = 14.0 if _paid_search_on() else 0.0
    if _paid_search_on() and partner_promo:
        paid_traffic *= 1.15
    if has_audience:
        organic = 25.0
        strat = 0.0
        if content_updates:
            strat += 14.0
        if regular_contact:
            strat += CONTACT_TRAFFIC_BONUS
        if partner_promo:
            strat *= 2.0
            promo = intensity * 0.50
        else:
            promo = intensity * 0.35
        base = organic + strat + promo + seo_traffic + paid_traffic
    else:
        promo = intensity * (1.5 if partner_promo else 1.0)
        base = promo + seo_traffic + paid_traffic
    return max(0.0, min(100.0, base))


def get_traffic():
    """Engaged traffic used for SALES.
    With audience + Partner OFF: only 50% of the 2k members visit
    (subtract half the organic floor). Members still exist — dial zero stays 2k.
    """
    base = get_traffic_potential()
    if has_audience and not partner_promo:
        # 50% of the 2k baseline members fail to engage → for sales only
        base = max(0.0, base - 12.5)
    return max(0.0, min(100.0, base))

def club_commission_on():
    for s in conversion_strategies:
        if s.get("is_multiplier") and s["checked"]:
            return True
    return False

def get_commission_capture():
    """Share of member purchases that actually pay affiliate commission.
    Without club-benefit framing, many members still buy on Amazon etc. (~35% leakage).
    With 'club gets the commission', members intentionally use the club link → ~100% capture.
    """
    if club_commission_on() and has_audience:
        return 1.0
    if has_audience:
        return 0.65  # loyalty leakage without explicit club benefit
    return 0.90  # cold traffic mostly uses the link they arrived on

def get_commission_proxy():
    traffic = get_traffic()
    conv = get_conversion()
    base = (traffic / 100.0) * (conv / 8.0)
    if has_audience:
        return base
    else:
        return base - (intensity / 100.0) * 1.0

def day_to_date(d):
    """Convert day index (0-based) to (month_index 0-11, day_of_month 1-based)."""
    remaining = d
    for mi, dim in enumerate(DAYS_PER_MONTH):
        if remaining < dim:
            return mi, remaining + 1
        remaining -= dim
    return 11, 25  # Dec 25

def current_month():
    mi, _ = day_to_date(min(day, TOTAL_DAYS - 1))
    return mi + 1

def current_day_in_month():
    _, dom = day_to_date(min(day, TOTAL_DAYS - 1))
    return dom

def current_date_str():
    mi, dom = day_to_date(min(day, TOTAL_DAYS - 1))
    return f"{MONTH_NAMES[mi]} {dom}"

def monitor_tint():
    """Return a colour bias for the monitor background based on money."""
    # money roughly -240 (all costs, no sales) to several hundred
    # map to a green/red tint
    if money >= 0:
        t = min(1.0, money / 300.0)
        r = int(18 + (1 - t) * 40)
        g = int(20 + t * 60)
        b = int(28 + (1 - t) * 20)
    else:
        t = min(1.0, abs(money) / 200.0)
        r = int(18 + t * 80)
        g = int(20 - t * 10)
        b = int(28 - t * 15)
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

def try_auto_sale():
    """Generate sales based on current traffic and conversion.
    Expected sales roughly proportional to traffic * conversion.
    Returns number of sales made this tick.
    """
    global money, total_revenue, total_commission, sales_count
    global last_sale_msg, last_sale_timer, flash_product_idx, flash_timer
    if not partner_promo:
        return 0  # no catalogue on the website without a partner
    if not products:
        return 0
    # Guarantee every product has a commission_rate
    for p in products:
        if "commission_rate" not in p:
            p["commission_rate"] = random.randint(8, 14) / 100.0
    conv = get_conversion()          # e.g. 1.0 – 8.0  (%)
    traffic = get_traffic()          # 0–100
    # Expected sales per day ≈ (traffic/100) * (conv/100) * scale
    # Scale chosen so decent setup gets a few sales per month
    # Real-world: sales ≈ visitors × conversion_rate
    # traffic dial 0–100 maps to relative visitor volume; conv is %
    # Scale so full traffic + 2% conv ≈ a few sales/day (playable but realistic)
    visitors_equiv = (traffic / 100.0) * 40.0   # full traffic ≈ 40 visitor-equivalents/day
    expected_per_day = visitors_equiv * (conv / 100.0)
    p = min(0.92, expected_per_day)
    made = 0
    if random.random() < p:
        prod = random.choice(products)
        rate = prod.get("commission_rate", COMMISSION_RATE)
        capture = get_commission_capture()
        commission = prod["price"] * rate * capture
        total_revenue += prod["price"]
        total_commission += commission
        club_earn = commission * 0.25
        money += club_earn  # community keeps 25%; club pays AdSpend
        sales_count += 1
        last_sale_msg = f"SOLD {prod['name']}  +${club_earn:,.0f}  ({int(prod.get('commission_rate', COMMISSION_RATE)*100)}%)"
        last_sale_timer = 2.0
        if audio_enabled and sale_sound:
            try:
                sale_sound.play()
            except Exception:
                pass
        # Flash the product + floating $ icon
        for i, pobj in enumerate(products):
            if pobj is prod or pobj["name"] == prod["name"]:
                flash_product_idx = i
                # Spawn rising coin/cash animation over the product card
                content_r = BROWSER_RECT.inflate(-14, -48)
                cols, gap, top = 3, 10, 8
                cw = (content_r.w - gap * (cols + 1)) // cols
                ch = 120
                col, row = i % cols, i // cols
                px = content_r.x + gap + col * (cw + gap) + cw // 2
                py = content_r.y + top + row * (ch + gap) + 40
                sale_anims.append({
                    "x": px, "y": py, "t": 0.0, "life": 0.9,
                    "text": f"+${commission:,.0f}", "vy": -55.0
                })
                break
        flash_timer = 0.6
        made = 1
        # Small chance of a second sale on the same tick if traffic/conv high
        if expected_per_day > 0.5 and random.random() < expected_per_day * 0.3:
            prod2 = random.choice(products)
            rate2 = prod2.get("commission_rate", COMMISSION_RATE)
            capture2 = get_commission_capture()
            commission2 = prod2["price"] * rate2 * capture2
            total_revenue += prod2["price"]
            total_commission += commission2
            club_earn2 = commission2 * 0.25
            money += club_earn2
            sales_count += 1
            last_sale_msg = f"SOLD {prod2['name']}  +${club_earn2:,.0f}  ({int(prod2.get('commission_rate', COMMISSION_RATE)*100)}%)"
            last_sale_timer = 2.0
            for i, pobj in enumerate(products):
                if pobj is prod2 or pobj["name"] == prod2["name"]:
                    flash_product_idx = i
                    break
            flash_timer = 0.6
            made = 2
    return made

def draw_rounded_rect(surface, color, rect, radius=8, width=0):
    pygame.draw.rect(surface, color, rect, width, border_radius=radius)

def draw_knob(surface, center, radius, value, max_value, label, accent_color, zero_label=None):
    """Dial only — strategy headings are drawn separately nearer the tickboxes."""
    pygame.draw.circle(surface, DARK_GRAY, center, radius)
    pygame.draw.circle(surface, accent_color, center, radius, 5)
    pygame.draw.circle(surface, (28, 30, 40), center, radius - 8)
    for i in range(11):
        a = math.radians(-140 + (i / 10) * 280)
        x1 = center[0] + (radius - 14) * math.sin(a)
        y1 = center[1] - (radius - 14) * math.cos(a)
        x2 = center[0] + (radius - 6) * math.sin(a)
        y2 = center[1] - (radius - 6) * math.cos(a)
        pygame.draw.line(surface, GRAY, (x1, y1), (x2, y2), 2)
    if zero_label:
        a0 = math.radians(-140)
        zx = center[0] + (radius + 6) * math.sin(a0)
        zy = center[1] - (radius + 6) * math.cos(a0)
        ztxt = font_tiny.render(zero_label, True, GRAY)
        surface.blit(ztxt, (zx - ztxt.get_width()//2, zy - ztxt.get_height()//2))
    ratio = max(0.0, min(1.0, value / max_value if max_value else 0))
    angle = math.radians(-140 + ratio * 280)
    end_x = center[0] + (radius - 18) * math.sin(angle)
    end_y = center[1] - (radius - 18) * math.cos(angle)
    pygame.draw.line(surface, WHITE, center, (end_x, end_y), 5)
    pygame.draw.circle(surface, accent_color, center, 8)
    pygame.draw.circle(surface, WHITE, center, 4)


def draw_strategy_heading(surface, col_rect, title, accent, kind, t):
    """Animated heading above the tickboxes — links dials to strategies."""
    import math as _m
    # Sit just above first strategy row
    base_y = STRATEGY_START_Y - 28
    # Soft pulse / shimmer
    pulse = 0.5 + 0.5 * _m.sin(t * 2.2 + (0.0 if kind == "traffic" else 1.2))
    glow = int(30 + 40 * pulse)

    # Accent underline that grows
    line_w = int((col_rect.w - 40) * (0.55 + 0.45 * pulse))
    lx = col_rect.centerx - line_w // 2
    ly = base_y + 22
    pygame.draw.rect(surface, (*accent[:3],), (lx, ly, line_w, 2), border_radius=1)
    # Soft glow line
    glow_surf = pygame.Surface((line_w + 8, 6), pygame.SRCALPHA)
    glow_surf.fill((accent[0], accent[1], accent[2], 40 + int(30 * pulse)))
    surface.blit(glow_surf, (lx - 4, ly - 2))

    # Title metrics first so icon + text can be centered as a unit
    bob = int(_m.sin(t * 2.5 + (0 if kind == "traffic" else 1)) * 1.5)
    col = (
        min(255, int(200 + 55 * pulse)),
        min(255, int(200 + 55 * pulse)),
        min(255, int(210 + 45 * pulse)),
    )
    col = (
        int(col[0] * 0.55 + accent[0] * 0.45),
        int(col[1] * 0.55 + accent[1] * 0.45),
        int(col[2] * 0.55 + accent[2] * 0.45),
    )
    txt = font_med_bold.render(title, True, col)
    icon_w = 22
    gap = 8
    total_w = icon_w + gap + txt.get_width()
    left = col_rect.centerx - total_w // 2
    iy = base_y + bob
    ix = left

    if kind == "traffic":
        # Signal bars
        for i, h in enumerate((5, 9, 13, 10)):
            bx = ix + 2 + i * 5
            by = iy + 16 - h
            c = (
                min(255, accent[0] + int(40 * pulse)),
                min(255, accent[1] + int(20 * pulse)),
                min(255, accent[2]),
            )
            pygame.draw.rect(surface, c, (bx, by, 3, h), border_radius=1)
    else:
        # Conversion: clean bullseye (no overlapping arrow)
        cx, cy = ix + 10, iy + 9
        pygame.draw.circle(surface, accent, (cx, cy), 8, 2)
        pygame.draw.circle(surface, accent, (cx, cy), 4, 1)
        pygame.draw.circle(surface, accent, (cx, cy), 2)

    surface.blit(txt, (left + icon_w + gap, base_y + bob))


def lock_reason_for_traffic(kind):
    """Explain why a traffic strategy is locked and how to enable it."""
    if kind == "audience":
        if not partner_promo:
            return ("Locked: only your partner knows if you have an unmonetised engaged audience. "
                    "Enable Partner Promotion first.")
        return None
    if kind == "seo":
        if not partner_promo:
            return "Locked: SEO needs Partner Promotion — communities cannot run search optimisation alone."
        return None
    if kind == "contact":
        if not partner_promo:
            return "Locked: needs Partner Promotion first."
        if not has_audience:
            return "Locked: needs Has an Audience first."
        return None
    if kind == "content":
        if not has_audience:
            return ("Locked: regular content updates only help when you have an audience to come back. "
                    "They do not change search-engine traffic. Enable Has an Audience first.")
        return None
    return None

def lock_reason_for_conversion(s):
    """Explain why a conversion strategy is locked and how to enable it."""
    label = s["label"]
    if label == "Paid search":
        return None
    if label == "Product reviews":
        if not partner_promo:
            return "Locked: Product reviews need Partner Promotion — communities will not produce reviews without support."
        return None
    if s.get("is_multiplier"):
        if not has_audience:
            return "Locked: needs Has an Audience first."
        return None
    return None

def draw_checkbox(surface, x, y, checked, label, enabled=True):
    """Always show checked state; when disabled, dim but keep the tick visible."""
    box = pygame.Rect(x, y, CHECK_SIZE, CHECK_SIZE)
    if checked:
        # Keep green check visible even when locked for the year
        fill = (40, 140, 80) if not enabled else ACCENT_GREEN
        border = (120, 180, 140) if not enabled else WHITE
        pygame.draw.rect(surface, fill, box, border_radius=4)
        pygame.draw.rect(surface, border, box, 2, border_radius=4)
        pygame.draw.line(surface, WHITE, (x + 5, y + 11), (x + 9, y + 16), 3)
        pygame.draw.line(surface, WHITE, (x + 9, y + 16), (x + 17, y + 6), 3)
        txt_col = (180, 200, 190) if not enabled else WHITE
    else:
        fill = (50, 52, 62) if not enabled else DARK_GRAY
        border = (80, 82, 95) if not enabled else GRAY
        pygame.draw.rect(surface, fill, box, border_radius=4)
        pygame.draw.rect(surface, border, box, 2, border_radius=4)
        txt_col = DISABLED if not enabled else GRAY
    txt = font_small.render(label, True, txt_col)
    surface.blit(txt, (x + CHECK_SIZE + 8, y + 2))
    return pygame.Rect(x, y, 250, CHECK_SIZE + 8)

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for w in words:
        test = current + " " + w if current else w
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines

def _tooltip_sections(text):
    """Parse 'Title: body' segments into ordered (title, body) pairs.
    Plain text (no titles) becomes a single body section.
    """
    import re
    # Split on known section titles while keeping the title
    titles = (
        "What", "Needs", "Why", "Why it matters", "Effect", "Money", "Evidence",
        "Side effect", "Cost", "Source", "Prerequisite", "Reason", "USP",
    )
    pattern = r"(?=(?:%s):)" % "|".join(re.escape(t) for t in titles)
    parts = [p.strip() for p in re.split(pattern, text) if p and p.strip()]
    sections = []
    for part in parts:
        if ":" in part:
            title, body = part.split(":", 1)
            title = title.strip()
            body = body.strip()
            if title in titles or title in ("Why it matters",):
                sections.append((title.upper(), body))
            else:
                # Unknown "word:" — keep as plain
                if sections:
                    sections[-1] = (sections[-1][0], (sections[-1][1] + " " + part).strip())
                else:
                    sections.append((None, part))
        else:
            if sections:
                sections[-1] = (sections[-1][0], (sections[-1][1] + " " + part).strip())
            else:
                sections.append((None, part))
    if not sections:
        sections = [(None, text.strip())]
    return sections

def _wrap_tooltip_body(body, font, max_w):
    """Wrap body text; put URLs on their own line(s) in link blue."""
    import re
    url_re = re.compile(r"(https?://\S+)")
    chunks = url_re.split(body)
    lines = []
    for chunk in chunks:
        if not chunk:
            continue
        is_url = chunk.startswith("http://") or chunk.startswith("https://")
        if is_url:
            while chunk:
                if font.size(chunk)[0] <= max_w:
                    lines.append(("url", chunk))
                    break
                lo, hi = 1, len(chunk)
                best = 1
                while lo <= hi:
                    mid = (lo + hi) // 2
                    if font.size(chunk[:mid])[0] <= max_w:
                        best = mid
                        lo = mid + 1
                    else:
                        hi = mid - 1
                lines.append(("url", chunk[:best]))
                chunk = chunk[best:]
        else:
            for ln in wrap_text(chunk.strip(), font, max_w):
                if ln.strip():
                    lines.append(("text", ln))
    return lines

def draw_tooltip(surface, text, mouse_pos, anchor_rect=None, prefer_below=False):
    """Beautiful structured tooltip: titled sections, wrapped URLs, soft card."""
    if not text:
        return
    max_w = 340
    pad_x, pad_y = 12, 10
    title_font = font_tiny
    body_font = font_tiny
    title_h = title_font.get_height() + 1
    body_h = body_font.get_height() + 3

    # Section accent colours
    accent = {
        "WHAT": ACCENT_BLUE,
        "NEEDS": ACCENT_ORANGE,
        "WHY": (180, 160, 255),
        "WHY IT MATTERS": (180, 160, 255),
        "EFFECT": ACCENT_GREEN,
        "MONEY": (255, 150, 90),
        "COST": (255, 150, 90),
        "EVIDENCE": (140, 190, 230),
        "SIDE EFFECT": (255, 180, 100),
        "SOURCE": (120, 160, 200),
        "PREREQUISITE": ACCENT_ORANGE,
        "REASON": (180, 160, 255),
        "USP": ACCENT_GREEN,
    }
    url_col = (64, 168, 255)  # bright link blue

    sections = _tooltip_sections(text)
    # Build render list: list of (kind, surface_or_none, text, color)
    rows = []  # (kind, text, color, height)
    for title, body in sections:
        if title:
            rows.append(("title", title, accent.get(title, ACCENT_BLUE), title_h + 2))
        for kind, line in _wrap_tooltip_body(body, body_font, max_w - pad_x * 2):
            col = url_col if kind == "url" else WHITE
            rows.append((kind, line, col, body_h))
        rows.append(("gap", "", None, 4))

    # Drop trailing gap
    while rows and rows[-1][0] == "gap":
        rows.pop()

    box_h = pad_y * 2 + sum(r[3] for r in rows)
    box_w = max_w

    if prefer_below and anchor_rect is not None:
        x = anchor_rect.centerx - box_w // 2
        y = anchor_rect.bottom + 28
        if x < 10:
            x = 10
        if x + box_w > WIDTH - 10:
            x = WIDTH - 10 - box_w
        if y + box_h > HEIGHT - 10:
            y = max(10, anchor_rect.top - box_h - 8)
    else:
        x = mouse_pos[0] + 16
        y = mouse_pos[1] - box_h - 8
        if x + box_w > WIDTH - 10:
            x = mouse_pos[0] - box_w - 16
        if y < 10:
            y = mouse_pos[1] + 20
        if y + box_h > HEIGHT - 10:
            y = HEIGHT - 10 - box_h

    rect = pygame.Rect(x, y, box_w, box_h)
    # Soft shadow
    shadow = pygame.Surface((box_w + 8, box_h + 8), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 60))
    surface.blit(shadow, (x + 3, y + 4))
    draw_rounded_rect(surface, TOOLTIP_BG, rect, radius=8)
    pygame.draw.rect(surface, TOOLTIP_BORDER, rect, 2, border_radius=8)
    # Left accent bar
    pygame.draw.rect(surface, ACCENT_BLUE, (x, y + 8, 3, box_h - 16), border_radius=2)

    cy = y + pad_y
    for kind, txt, col, h in rows:
        if kind == "gap":
            cy += h
            continue
        if kind == "title":
            # Title chip
            chip = title_font.render(txt, True, col)
            surface.blit(chip, (x + pad_x, cy))
            # Underline
            pygame.draw.line(surface, (*col[:3],), (x + pad_x, cy + title_h - 1),
                             (x + pad_x + chip.get_width(), cy + title_h - 1), 1)
        else:
            img = body_font.render(txt, True, col)
            surface.blit(img, (x + pad_x, cy))
            if kind == "url":
                pygame.draw.line(surface, col,
                                 (x + pad_x, cy + img.get_height() - 1),
                                 (x + pad_x + img.get_width(), cy + img.get_height() - 1), 1)
        cy += h

def product_card_rects():
    """Return list of (rect, product) for click detection."""
    content = BROWSER_RECT.inflate(-14, -48)
    content.top += 28
    card_w, card_h = 175, 145
    start_x = content.x + 15
    start_y = content.y + 15
    gap = 14
    result = []
    for i, prod in enumerate(products):
        col = i % 3
        row = i // 3
        cx = start_x + col * (card_w + gap)
        cy = start_y + row * (card_h + gap)
        result.append((pygame.Rect(cx, cy, card_w, card_h), prod))
    return result

def draw_browser_catalogue(surface, tint):
    draw_rounded_rect(surface, BROWSER_HEADER, BROWSER_RECT, radius=10)
    content = BROWSER_RECT.inflate(-14, -48)
    content.top += 28
    # Tint the content area based on money
    bg = (
        min(255, BROWSER_BG[0] + tint[0] - 18),
        min(255, BROWSER_BG[1] + tint[1] - 20),
        min(255, BROWSER_BG[2] + tint[2] - 28),
    )
    draw_rounded_rect(surface, bg, content, radius=6)
    # Traffic-light toolbar first, then title to the right (no overlap)
    pygame.draw.circle(surface, RED, (BROWSER_RECT.x + 18, BROWSER_RECT.y + 18), 6)
    pygame.draw.circle(surface, ACCENT_ORANGE, (BROWSER_RECT.x + 36, BROWSER_RECT.y + 18), 6)
    pygame.draw.circle(surface, ACCENT_GREEN, (BROWSER_RECT.x + 54, BROWSER_RECT.y + 18), 6)
    site = club_site_url or "yourclub.com"
    title = font_med_bold.render(
        f"Web Catalogue  –  {site}" if partner_promo else "Web Catalogue  –  (no club site)",
        True, WHITE)
    surface.blit(title, (BROWSER_RECT.x + 72, BROWSER_RECT.y + 10))
    url_rect = pygame.Rect(BROWSER_RECT.x + 16, BROWSER_RECT.y + 38, 420, 22)
    draw_rounded_rect(surface, (25, 28, 38), url_rect, radius=5)
    if partner_promo and club_site_url:
        url_txt = font_tiny.render(f"  https://{club_site_url}/catalogue", True, GRAY)
    else:
        url_txt = font_tiny.render("  (no website — partner required to host catalogue)", True, DARK_GRAY)
    surface.blit(url_txt, (url_rect.x + 4, url_rect.y + 4))

    if not partner_promo:
        # You have no website to put a catalogue on without a partner customer
        msg1 = font_med_bold.render("No club website", True, GRAY)
        msg2 = font_small.render("Enable Partner Promotion — they recommend a club and put Smart Catalogue on its page.", True, (140, 150, 170))
        msg3 = font_tiny.render("Without a partner there is no site to log into and no storefront — and no sales.", True, DARK_GRAY)
        surface.blit(msg1, (content.centerx - msg1.get_width() // 2, content.centery - 36))
        surface.blit(msg2, (content.centerx - msg2.get_width() // 2, content.centery - 8))
        surface.blit(msg3, (content.centerx - msg3.get_width() // 2, content.centery + 18))
    else:
        cards = product_card_rects()
        for idx, (rect, prod) in enumerate(cards):
            if idx == flash_product_idx and flash_timer > 0:
                flash_col = (255, 255, 180) if (int(flash_timer * 10) % 2 == 0) else (255, 200, 60)
                draw_rounded_rect(surface, flash_col, rect.inflate(6, 6), radius=10)
            draw_rounded_rect(surface, CARD_BG, rect, radius=8)
            swatch = pygame.Rect(rect.x + 10, rect.y + 10, rect.w - 20, 68)
            draw_rounded_rect(surface, prod["color"], swatch, radius=6)
            name = font_small.render(prod["name"][:22], True, WHITE)
            price = font_med_bold.render(f"${prod['price']:,.2f}", True, ACCENT_GREEN)
            rate = prod.get("commission_rate", COMMISSION_RATE)
            rate_txt = font_tiny.render(f"{int(rate * 100)}% commission", True, ACCENT_ORANGE)
            surface.blit(name, (rect.x + 10, rect.y + 84))
            surface.blit(price, (rect.x + 10, rect.y + 104))
            surface.blit(rate_txt, (rect.x + 10, rect.y + 126))

def draw_monitor_frame(surface):
    outer = MONITOR_RECT.inflate(28, 38)
    outer.top -= 8
    draw_rounded_rect(surface, BEZEL, outer, radius=16)
    draw_rounded_rect(surface, MONITOR_INNER, MONITOR_RECT, radius=8)
    pygame.draw.rect(surface, BEZEL, (MONITOR_RECT.centerx - 36, MONITOR_RECT.bottom + 6, 72, 16), border_radius=4)
    pygame.draw.rect(surface, BEZEL, (MONITOR_RECT.centerx - 80, MONITOR_RECT.bottom + 20, 160, 12), border_radius=5)

def draw_equation(surface, intensity_val, conv_val, comm_proxy, holding=False):
    fixed_size = 28
    op_size = 28
    if comm_proxy > 0:
        comm_size = int(fixed_size + min(1.0, comm_proxy) * 50)
        if comm_proxy > 0.55:
            comm_col = (255, 200, 40)
        else:
            g = min(255, 120 + int(comm_proxy * 135))
            comm_col = (40, g, min(255, 100 + int(comm_proxy * 100)))
    else:
        shrink = max(0.0, 1.0 + comm_proxy)
        comm_size = int(16 + shrink * (fixed_size - 16))
        intensity_r = min(1.0, abs(comm_proxy))
        r = int(180 + intensity_r * 75)
        g = int(60 - intensity_r * 40)
        b = int(60 - intensity_r * 40)
        comm_col = (max(120, r), max(20, g), max(20, b))

    show_adspend = holding and intensity > 1.0  # promote always costs
    font_fixed = get_font(fixed_size, bold=True)
    font_m = get_font(comm_size, bold=True)
    font_op = get_font(op_size, bold=True)

    txt_p = font_fixed.render("PROMOTION", True, ACCENT_BLUE)
    txt_x = font_op.render("×", True, WHITE)
    txt_c = font_fixed.render("CONVERSION", True, ACCENT_ORANGE)
    txt_eq = font_op.render("=", True, WHITE)
    txt_m = font_m.render("COMMISSION", True, comm_col)

    parts = [txt_p, txt_x, txt_c, txt_eq, txt_m]
    if show_adspend:
        txt_minus = font_op.render("−", True, WHITE)
        txt_ad = font_fixed.render("AdSpend", True, (255, 140, 80))
        parts.extend([txt_minus, txt_ad])

    total_w = sum(p.get_width() for p in parts) + 8 * (len(parts) - 1)
    start_x = max(20, (WIDTH - total_w) // 2)
    baseline = EQUATION_Y + 36
    for p in parts:
        surface.blit(p, (start_x, baseline - p.get_height() // 2))
        start_x += p.get_width() + 8

LOSS_PROMOTE_LIMIT = -100.0  # club will not fund promote beyond this loss
EARLY_CONTRACT_LOSS = -1000.0  # community ends contract mid-year if loss exceeds $1k

def draw_hold_button(surface, active, enabled=True, locked=False, cooldown=0.0, loss_locked=False):
    """Max 1s continuous hold, then 3s cooldown. Blocked if club is >$100 in the red."""
    if not enabled:
        label = "HOLD TO PROMOTE"
        color = DISABLED
        txt_col = GRAY
        border = DARK_GRAY
        hint_msg = "Available after START YEAR"
    elif loss_locked:
        label = "PROMOTE BLOCKED"
        color = (70, 40, 45)
        txt_col = (255, 160, 160)
        border = RED
        hint_msg = "Club won't fund more losses (over $100 down)"
    elif locked or cooldown > 0:
        secs = max(0.1, cooldown)
        label = f"COOLDOWN {secs:.1f}s"
        color = (90, 50, 55)
        txt_col = (255, 180, 180)
        border = RED
        hint_msg = "Max 1s hold — wait 3s before promoting again"
    else:
        label = "HOLD TO PROMOTE" if not active else "PROMOTING..."
        color = GLOW_GREEN if active else ACCENT_GREEN
        txt_col = BLACK if active else WHITE
        border = WHITE if active else GRAY
        hint_msg = "Max 1s hold · then 3s cooldown"
    draw_rounded_rect(surface, color, PROMOTE_RECT, radius=12)
    pygame.draw.rect(surface, border, PROMOTE_RECT, 3, border_radius=12)
    txt = font_large.render(label, True, txt_col)
    surface.blit(txt, (PROMOTE_RECT.centerx - txt.get_width() // 2,
                       PROMOTE_RECT.centery - txt.get_height() // 2))
    hint = font_tiny.render(hint_msg, True, GRAY)
    surface.blit(hint, (PROMOTE_RECT.centerx - hint.get_width() // 2, PROMOTE_RECT.bottom + 8))

def get_hud_rect():
    """HUD under conversion strategies — compact two-column layout."""
    return pygame.Rect(CONV_COL.x + 8, 400, CONV_COL.w - 16, 155)

def get_quit_rect():
    """Quit button at bottom of HUD."""
    hud = get_hud_rect()
    return pygame.Rect(hud.x + 10, hud.bottom - 30, hud.w - 20, 24)

def draw_quit_button(surface, rect):
    draw_rounded_rect(surface, (160, 50, 55), rect, radius=8)
    pygame.draw.rect(surface, (255, 110, 110), rect, 2, border_radius=8)
    txt = font_med_bold.render("QUIT YEAR", True, WHITE)
    surface.blit(txt, (rect.centerx - txt.get_width() // 2,
                       rect.centery - txt.get_height() // 2))



def draw_checkered_flag(surface, rect, t=0.0, large=False, mirror=False):
    """Beautiful waving checkered flag — fabric ripple, soft shading, metal pole."""
    import math as _m
    # Work on a temp surface for soft edges
    pad = 8 if large else 4
    w = max(24, rect.w)
    h = max(16, rect.h)
    flag_surf = pygame.Surface((w + pad * 2 + 12, h + pad * 2 + 8), pygame.SRCALPHA)

    pole_x = 6 if not mirror else flag_surf.get_width() - 6
    # Metallic pole with highlight
    for i, col in enumerate([(90, 95, 110), (200, 205, 220), (240, 242, 250), (160, 165, 180)]):
        pygame.draw.line(flag_surf, col, (pole_x - 1 + i // 2, 2), (pole_x - 1 + i // 2, h + pad + 4), 1)
    # Gold finial
    pygame.draw.circle(flag_surf, (255, 210, 90), (pole_x, 3), 3)
    pygame.draw.circle(flag_surf, (255, 240, 180), (pole_x - 1, 2), 1)

    cols = 10 if large else 7
    rows = 7 if large else 5
    cloth_w = w - 4
    cloth_h = h - 2
    cell_w = cloth_w / cols
    cell_h = cloth_h / rows
    amp = (5.5 if large else 3.0)
    phase = t * 5.5

    # Draw fabric as vertical strips with sine displacement (wave travels along flag)
    for c in range(cols):
        for r in range(rows):
            # Wave: stronger toward free edge, travels over time
            edge = c / max(1, cols - 1)
            if mirror:
                edge = 1.0 - edge
            ripple = _m.sin(phase + c * 0.55 + r * 0.15) * amp * (0.25 + 0.75 * edge)
            ripple2 = _m.sin(phase * 1.3 + c * 0.9) * amp * 0.35 * edge
            dx = ripple + ripple2
            # Shade: brighter on crest, darker in trough
            shade = 0.72 + 0.28 * (0.5 + 0.5 * _m.sin(phase + c * 0.55))
            base_light = (r + c) % 2 == 0
            if base_light:
                col = (int(250 * shade), int(250 * shade), int(252 * shade), 255)
            else:
                col = (int(18 * shade + 8), int(18 * shade + 8), int(22 * shade + 10), 255)
            if mirror:
                x0 = pole_x - 3 - (c + 1) * cell_w + dx
            else:
                x0 = pole_x + 3 + c * cell_w + dx
            y0 = pad + r * cell_h + _m.sin(phase * 0.7 + c * 0.3) * 0.8 * edge
            rw = max(2, int(cell_w) + 1)
            rh = max(2, int(cell_h) + 1)
            pygame.draw.rect(flag_surf, col, (int(x0), int(y0), rw, rh))

    # Soft outline along free edge for depth
    for i in range(rows):
        edge = 1.0
        ripple = _m.sin(phase + (cols - 1) * 0.55 + i * 0.15) * amp * edge
        if mirror:
            x = pole_x - 3 - cols * cell_w + ripple
        else:
            x = pole_x + 3 + cols * cell_w + ripple
        y = pad + i * cell_h
        pygame.draw.line(flag_surf, (0, 0, 0, 50), (int(x), int(y)), (int(x), int(y + cell_h)), 1)

    surface.blit(flag_surf, (rect.x - pad, rect.y - pad))

def draw_flag_button(surface, t):
    """Setup-only: reopen last year-end P&L — premium animated flag control."""
    if not last_gameover_available:
        return
    import math as _m
    # Pulsing soft glow behind the flag
    pulse = 0.5 + 0.5 * _m.sin(t * 2.5)
    glow_col = (40 + int(30 * pulse), 50 + int(25 * pulse), 80 + int(40 * pulse))
    glow = pygame.Rect(FLAG_RECT.x - 6, FLAG_RECT.y - 6, FLAG_RECT.w + 12, FLAG_RECT.h + 14)
    draw_rounded_rect(surface, glow_col, glow, radius=8)
    pygame.draw.rect(surface, (100, 140, 200), glow, 1, border_radius=8)
    draw_checkered_flag(surface, FLAG_RECT, t=t, large=True)
    tip = font_tiny.render("Last results", True, (160, 190, 230))
    surface.blit(tip, (FLAG_RECT.centerx - tip.get_width() // 2, FLAG_RECT.bottom + 4))

def draw_audio_button(surface):
    """Round sound control — bottom-right of the monitor."""
    cx, cy = AUDIO_RECT.centerx, AUDIO_RECT.centery
    r = AUDIO_RECT.w // 2
    if audio_enabled:
        fill, border, tcol = (32, 90, 68), ACCENT_GREEN, WHITE
        ring = (80, 200, 140)
    else:
        fill, border, tcol = (55, 32, 36), RED, (230, 170, 170)
        ring = (200, 80, 90)

    # Soft outer glow
    glow = pygame.Surface((r * 2 + 12, r * 2 + 12), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*border, 45), (r + 6, r + 6), r + 5)
    surface.blit(glow, (cx - r - 6, cy - r - 6))

    # Disc
    pygame.draw.circle(surface, fill, (cx, cy), r)
    pygame.draw.circle(surface, ring, (cx, cy), r, 2)
    pygame.draw.circle(surface, (255, 255, 255, 30) if False else (50, 55, 70), (cx, cy), r - 3, 1)

    # Speaker icon centered
    ix, iy = cx - 6, cy
    cone = [(ix - 4, iy - 5), (ix + 2, iy - 5), (ix + 8, iy - 9),
            (ix + 8, iy + 9), (ix + 2, iy + 5), (ix - 4, iy + 5)]
    pygame.draw.polygon(surface, tcol, cone)
    pygame.draw.rect(surface, tcol, (ix - 7, iy - 4, 4, 8), border_radius=1)
    if audio_enabled:
        pygame.draw.arc(surface, tcol, (ix + 6, iy - 7, 9, 14), -0.85, 0.85, 2)
        pygame.draw.arc(surface, tcol, (ix + 10, iy - 10, 11, 20), -0.85, 0.85, 2)
    else:
        pygame.draw.line(surface, RED, (cx - 10, cy - 10), (cx + 10, cy + 10), 3)
        pygame.draw.line(surface, RED, (cx + 10, cy - 10), (cx - 10, cy + 10), 3)

def draw_randomise_button(surface, enabled=True):
    if enabled:
        draw_rounded_rect(surface, (50, 70, 110), RANDOMISE_RECT, radius=8)
        pygame.draw.rect(surface, ACCENT_BLUE, RANDOMISE_RECT, 2, border_radius=8)
        txt = font_small.render("RANDOMISE PARTS", True, WHITE)
    else:
        draw_rounded_rect(surface, (40, 42, 55), RANDOMISE_RECT, radius=8)
        pygame.draw.rect(surface, DARK_GRAY, RANDOMISE_RECT, 2, border_radius=8)
        txt = font_small.render("RANDOMISE PARTS", True, DISABLED)
    surface.blit(txt, (RANDOMISE_RECT.centerx - txt.get_width() // 2,
                       RANDOMISE_RECT.centery - txt.get_height() // 2))

def draw_start_button(surface):
    draw_rounded_rect(surface, ACCENT_ORANGE, START_RECT, radius=12)
    pygame.draw.rect(surface, WHITE, START_RECT, 3, border_radius=12)
    txt = font_large.render("START YEAR", True, BLACK)
    surface.blit(txt, (START_RECT.centerx - txt.get_width() // 2,
                       START_RECT.centery - txt.get_height() // 2))
    hint = font_tiny.render("Lock strategies & begin", True, GRAY)
    surface.blit(hint, (START_RECT.centerx - hint.get_width() // 2, START_RECT.bottom + 8))

def draw_game_over(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    box = pygame.Rect(WIDTH // 2 - 270, HEIGHT // 2 - 320, 540, 640)
    draw_rounded_rect(surface, PANEL_BG, box, radius=16)
    pygame.draw.rect(surface, ACCENT_ORANGE, box, 3, border_radius=16)

    title = font_huge.render("YEAR-END P&L", True, WHITE)
    surface.blit(title, (box.centerx - title.get_width() // 2, box.y + 14))
    # Year number under the title (career year that just finished)
    yr = 1
    if last_pnl is not None and last_pnl.get("years_completed") is not None:
        yr = max(1, int(last_pnl.get("years_completed", 1)))
    elif years_completed > 0:
        yr = years_completed
    year_lbl = font_med_bold.render(f"Year {yr}", True, ACCENT_ORANGE)
    surface.blit(year_lbl, (box.centerx - year_lbl.get_width() // 2, box.y + 52))
    # Animated checkered flags flanking the title — full wave, mirrored pair
    fl = pygame.Rect(box.x + 22, box.y + 10, 56, 36)
    fr = pygame.Rect(box.right - 78, box.y + 10, 56, 36)
    draw_checkered_flag(surface, fl, t=flag_anim_t, large=True, mirror=False)
    draw_checkered_flag(surface, fr, t=flag_anim_t + 0.35, large=True, mirror=True)

    # Who gets what: Platform / Partner / Community
    partner_fee = max(0.0, total_costs - total_adspend)  # $20/mo only when Partner Promotion was on
    has_partner = partner_fee > 0 or (partner_promo and not viewing_historical_pnl)
    plat_c = total_commission * 0.50
    part_c = total_commission * 0.25
    comm_c = total_commission * 0.25
    # AdSpend routing:
    # - Paid search always goes to Google/external (never the partner).
    # - Promote goes to the partner only when engaging OUR OWN members (has audience + partner).
    # - Cold promote (no audience) is external paid acquisition.
    promote_spend = float(total_promote_adspend)
    paid_spend = float(total_paidsearch_adspend)
    if promote_spend + paid_spend <= 0 and total_adspend > 0:
        promote_spend = float(total_adspend)
        paid_spend = 0.0
    engage_own = has_partner and has_audience
    if engage_own:
        # Promoting to our members — materials/ops through the partner
        promote_to_partner = promote_spend
        promote_external = 0.0
    else:
        promote_to_partner = 0.0
        promote_external = promote_spend
    # Paid search is always external (Google etc.)
    paid_external = paid_spend
    adspend_to_partner = promote_to_partner
    external_adspend = promote_external + paid_external
    partner_gets = (part_c + partner_fee + adspend_to_partner) if has_partner else 0.0
    community_gets = comm_c - total_adspend - (partner_fee if has_partner else 0.0)
    net = money  # still used for contract rules / high scores

    # Rows: (label, value, is_expense, help, level)
    rows = [
        ("Sales completed", sales_count, False,
         "Number of successful product sales completed this year.", 0),
        ("Gross sales value", total_revenue, False,
         "Total retail value of products sold through your catalogue this year.", 0),
        ("Gross commission", total_commission, False,
         "Gross affiliate commission (10–30% per product × capture rate).", 1),
        ("WHO GETS WHAT", None, False,
         "How gross commission, AdSpend, and the partner fee are shared.", 0),
        ("Platform", plat_c, False,
         "Platform receives 50% of gross commission.", 2),
    ]
    if has_partner:
        rows += [
            ("Partner", partner_gets, False,
             "Partner receives 25% of gross commission, the $20/mo engagement fee, and paid-search "
             "promote spend only when engaging your own audience (member materials through the partner). Paid search always goes to Google/external — never to the partner.", 2),
            ("  commission share", part_c, False,
             "25% of gross affiliate commission.", 3),
            ("  engagement fee", partner_fee, False,
             "Community pays $20/mo to the partner while Partner Promotion is on.", 3),
            ("  AdSpend received", adspend_to_partner, False,
             "Partner-routed adspend: promote spend used to engage your own members (not paid search).", 3),
            ("Community", community_gets, False,
             "Community keeps 25% of gross commission, then pays AdSpend and the $20/mo partner fee.", 2),
            ("  Promote to partner", -promote_to_partner, True,
             "Promote cost to the partner when Has an Audience — engaging own members. 2x with SEO/paid links.", 3),
            ("  Promote (external)", -promote_external, True,
             "Promote paid externally (cold acquisition or no partner). 2x with SEO/paid links.", 3),
            ("  Paid search (Google)", -paid_spend, True,
             "Always-on paid search — always paid to Google/external platforms, never to the partner.", 3),
            ("  Fee to partner", -partner_fee, True,
             "Community pays $20/mo to the partner for engagement / consultancy. "
             "No fee when Partner Promotion is off.", 3),
        ]
    else:
        rows += [
            ("Partner", 0.0, False,
             "No partner engaged — Partner Promotion was off. Partner receives nothing "
             "and the community does not pay the $20/mo fee.", 2),
            ("Community", community_gets, False,
             "Community keeps 25% of gross commission and pays any AdSpend directly "
             "(no partner fee without Partner Promotion).", 2),
            ("  Promote (external)", -promote_spend, True,
             "Promote cost — always external. 2x when SEO or paid-search links are active.", 3),
            ("  Paid search (external)", -paid_spend, True,
             "Always-on paid search paid externally (no partner engaged).", 3),
        ]

    y = box.y + 78
    pnl_hover_rects = []  # (rect, help_text) for rollover
    for label, val, is_exp, help_txt, level in rows:
        x0 = box.x + {0: 36, 1: 48, 2: 68, 3: 84}.get(level, 36)
        if val is None:
            lt = font_med_bold.render(label, True, ACCENT_ORANGE)
            surface.blit(lt, (box.x + 36, y))
            row_rect = pygame.Rect(box.x + 30, y - 2, box.w - 60, 22)
            pnl_hover_rects.append((row_rect, help_txt))
            y += 22
            continue
        col = RED if val < 0 else (ACCENT_GREEN if val > 0 else GRAY)
        if label == "Sales completed":
            lt = font_med.render(label, True, GRAY)
            vt = font_med_bold.render(f"{int(val)}", True, WHITE if val == 0 else ACCENT_GREEN)
        elif level == 1:
            # Gross as section total — slightly larger
            lt = font_med_bold.render(label, True, WHITE)
            vt = font_large.render(f"${val:+,.0f}" if val != 0 else "$0", True, col)
        else:
            lt = font_med.render(label, True, GRAY)
            vt = font_med_bold.render(f"${val:+,.0f}" if val != 0 else "$0", True, col)
        surface.blit(lt, (x0, y))
        surface.blit(vt, (box.right - 36 - vt.get_width(), y))
        row_rect = pygame.Rect(box.x + 30, y - 2, box.w - 60, 24 if level == 1 else 22)
        pnl_hover_rects.append((row_rect, help_txt))
        y += 26 if level == 1 else 24
    # Store for main-loop hover (module-level list)
    global _pnl_hover_rects
    _pnl_hover_rects = pnl_hover_rects

    # Divider
    pygame.draw.line(surface, GRAY, (box.x + 30, y + 4), (box.right - 30, y + 4), 1)
    y += 16

    year_net = float(net)  # community result — used for contract rules only
    # Why the community ends the contract
    if just_finished_loss and not viewing_historical_pnl:
        reason = (last_pnl or {}).get("loss_reason")
        prev = (last_pnl or {}).get("last_year_net")
        # Headline
        head = font_med_bold.render("CONTRACT ENDED BY THE COMMUNITY", True, RED)
        surface.blit(head, (box.centerx - head.get_width() // 2, y))
        y += 22
        if reason == "worse_than_last":
            prev = (last_pnl or {}).get("compared_to_year", prev)
            prev_s = f"${float(prev):,.0f}" if prev is not None else "n/a"
            lines = [
                "They got rid of you — community share fell more than 50% vs last year.",
                f"Community share last year: {prev_s}  ·  This year: ${year_net:,.0f}",
                "Compared on community share only (not gross commission).",
            ]
        elif reason == "not_worth":
            lines = [
                "They got rid of you because the return was too small.",
                f"Community net ${year_net:,.0f} is under the $600 minimum.",
                "After the first year, under $600 is not worth keeping the catalogue.",
            ]
        elif reason == "early_loss":
            lines = [
                "They ended the contract early — losses passed $1,000.",
                f"Community net hit ${year_net:,.0f} before year-end.",
                "The community will not keep funding a catalogue that deep in the red.",
            ]
        elif reason == "loss":
            lines = [
                "They got rid of you because the catalogue lost money.",
                f"Community net finished at ${year_net:,.0f}.",
                "The club will not keep a storefront that drains the community share.",
            ]
        else:
            lines = [
                "The community has ended your catalogue contract.",
                "Results did not meet their standard for keeping the storefront.",
            ]
        for line in lines:
            t = font_tiny.render(line, True, (255, 180, 180))
            surface.blit(t, (box.centerx - t.get_width() // 2, y))
            y += 16
        y += 6
    elif (last_pnl or {}).get("disappointment") and not viewing_historical_pnl:
        # Tolerated decline (≤25%) — still CONTINUE, but community is disappointed
        prev = (last_pnl or {}).get("compared_to_year")
        prev_s = f"${float(prev):,.0f}" if prev is not None else "n/a"
        head = font_med_bold.render("Community note", True, ACCENT_ORANGE)
        surface.blit(head, (box.centerx - head.get_width() // 2, y))
        y += 20
        lines = [
            "They're disappointed — profit is down on last year.",
            f"Community share last year: {prev_s}  ·  This year: ${year_net:,.0f}",
            "Compared on community share only. A decline of up to 50% is accepted.",
        ]
        for line in lines:
            t = font_tiny.render(line, True, (255, 200, 140))
            surface.blit(t, (box.centerx - t.get_width() // 2, y))
            y += 16
        y += 6
    else:
        y += 12

    # High scores — top 3 (click to recall settings for next game)
    y += 8
    hs_title = font_med_bold.render("TOP SCORES  ·  click to load setup", True, ACCENT_BLUE)
    surface.blit(hs_title, (box.centerx - hs_title.get_width() // 2, y))
    y += 26
    hs_rects = []
    medals = ["1st", "2nd", "3rd"]
    import math as _m
    for i in range(3):
        row_r = pygame.Rect(box.x + 36, y, box.w - 72, 28)
        if i < len(high_scores):
            e = high_scores[i]
            entry_net = float(e.get("net", 0))
            ncol = ACCENT_GREEN if entry_net >= 0 else RED
            sales_n = int(e.get("sales", 0))
            is_cur = bool(e.get("is_current"))
            # Match current P&L if flag missing (reopened snapshot)
            if not is_cur and last_pnl is not None:
                if abs(float(e.get("net", 0)) - float(last_pnl.get("money", -999999))) < 0.5:
                    if int(e.get("sales", -1)) == int(last_pnl.get("sales_count", -2)):
                        is_cur = True

            if is_cur:
                # Pulsing gold highlight — this is THIS year
                pulse = 0.5 + 0.5 * _m.sin(flag_anim_t * 4.0)
                fill = (
                    int(40 + 50 * pulse),
                    int(50 + 40 * pulse),
                    int(20 + 10 * pulse),
                    220,
                )
                glow = pygame.Surface((row_r.w, row_r.h), pygame.SRCALPHA)
                glow.fill(fill)
                surface.blit(glow, row_r.topleft)
                border_col = (
                    int(200 + 55 * pulse),
                    int(170 + 50 * pulse),
                    int(40 + 30 * pulse),
                )
                pygame.draw.rect(surface, border_col, row_r, 2, border_radius=6)
                badge = font_tiny.render("THIS YEAR", True, (255, 230, 120))
                left = font_small.render(
                    f"{medals[i]}  ${entry_net:,.0f}   ({sales_n:,} sales)", True, (255, 245, 180)
                )
                surface.blit(left, (row_r.x + 6, row_r.y + 6))
                surface.blit(badge, (row_r.right - badge.get_width() - 8, row_r.y + 7))
                # Sparkle ticks on the sides
                for sx in (row_r.x + 2, row_r.right - 4):
                    sy = row_r.centery + int(_m.sin(flag_anim_t * 6 + sx) * 4)
                    pygame.draw.circle(surface, (255, 240, 150), (sx, sy), 2)
            else:
                left = font_small.render(
                    f"{medals[i]}  ${entry_net:,.0f}   ({sales_n:,} sales)", True, ncol
                )
                right = font_tiny.render("Load setup →", True, GRAY)
                surface.blit(left, (row_r.x + 6, row_r.y + 6))
                surface.blit(right, (row_r.right - right.get_width() - 6, row_r.y + 8))
                pygame.draw.rect(surface, (60, 80, 110), row_r, 1, border_radius=4)
            hs_rects.append((row_r, e))
        else:
            empty = font_small.render(f"{medals[i]}  —", True, DARK_GRAY)
            surface.blit(empty, (row_r.x + 6, row_r.y + 6))
        y += 30

    global _hs_click_rects
    _hs_click_rects = hs_rects

    # Catalogue Lost only when THIS year just finished in a loss.
    # Reopening last results via flag always shows CONTINUE.
    global _gameover_btn_rect, _gameover_show_lost
    ng = pygame.Rect(box.centerx - 120, box.bottom - 56, 240, 44)
    show_lost = (not viewing_historical_pnl) and just_finished_loss
    _gameover_btn_rect = ng
    _gameover_show_lost = show_lost
    if show_lost:
        draw_rounded_rect(surface, (160, 40, 50), ng, radius=10)
        pygame.draw.rect(surface, (255, 100, 110), ng, 2, border_radius=10)
        ngt = font_large.render("CATALOGUE LOST", True, WHITE)
    else:
        draw_rounded_rect(surface, ACCENT_GREEN, ng, radius=10)
        ngt = font_large.render("CONTINUE", True, BLACK)
    surface.blit(ngt, (ng.centerx - ngt.get_width() // 2, ng.centery - ngt.get_height() // 2))
    return ng

def draw_welcome(surface, t):
    """Original soft sim-style intro — loops until the player clicks."""
    surface.fill(BG)
    # Loop the cinematic cycle (0→1→0…) so animation never freezes
    cycle = max(0.5, WELCOME_DURATION)
    phase = (t % cycle) / cycle
    # Hold full opacity for most of the loop; brief soft pulse at edges
    if phase < 0.08:
        alpha = phase / 0.08
    elif phase < 0.92:
        alpha = 1.0
    else:
        alpha = max(0.35, 1.0 - (phase - 0.92) / 0.08)

    def fade(color):
        return (
            int(color[0] * alpha + BG[0] * (1 - alpha)),
            int(color[1] * alpha + BG[1] * (1 - alpha)),
            int(color[2] * alpha + BG[2] * (1 - alpha)),
        )

    # Animated grid (OpenTTD / sim feel)
    grid = fade((32, 38, 52))
    spacing = 40
    offset = int((t * 18) % spacing)
    for x in range(-spacing, WIDTH + spacing, spacing):
        pygame.draw.line(surface, grid, (x + offset, 0), (x + offset, HEIGHT), 1)
    for y in range(-spacing, HEIGHT + spacing, spacing):
        pygame.draw.line(surface, grid, (0, y + offset // 2), (WIDTH, y + offset // 2), 1)

    import math as _math
    for i in range(12):
        ang = t * 0.35 + i * (2 * _math.pi / 12)
        rad = 160 + 40 * _math.sin(t * 0.8 + i)
        nx = WIDTH // 2 + int(_math.cos(ang) * rad)
        ny = HEIGHT // 2 + int(_math.sin(ang) * rad * 0.55)
        r = 3 + (i % 3)
        pygame.draw.circle(surface, fade((60, 120, 200)), (nx, ny), r)
        pygame.draw.line(surface, fade((40, 70, 110)), (WIDTH // 2, HEIGHT // 2 - 20), (nx, ny), 1)

    panel = pygame.Rect(WIDTH // 2 - 340, HEIGHT // 2 - 150, 680, 300)
    pygame.draw.rect(surface, fade((24, 28, 40)), panel, border_radius=16)
    pygame.draw.rect(surface, fade((70, 130, 200)), panel, 2, border_radius=16)

    # Gentle title scale pulse
    scale = 1.0 + 0.03 * _math.sin(t * 1.8)
    size_title = max(20, int(42 * scale))
    size_sub = max(14, int(20 * scale))
    f_title = get_font(size_title, bold=True)
    f_sub = get_font(size_sub, bold=False)
    f_tag = get_font(16)
    f_src = get_font(13)

    title = "Affiliate Marketing Simulator"
    author = "By Simon Barnett"
    tag = "Build traffic  ·  Convert members  ·  Grow commission"

    def blit_c(text, font, color, y):
        img = font.render(text, True, fade(color))
        surface.blit(img, (WIDTH // 2 - img.get_width() // 2, y - img.get_height() // 2))

    title_y = HEIGHT // 2 - 50
    blit_c(title, f_title, WHITE, title_y)
    lw = int(260 * alpha)
    if lw > 8:
        pygame.draw.rect(surface, fade(ACCENT_BLUE),
                         (WIDTH // 2 - lw // 2, HEIGHT // 2 - 20, lw, 3), border_radius=2)
    blit_c(author, f_sub, ACCENT_BLUE, HEIGHT // 2 + 8)
    blit_c(tag, f_tag, GRAY, HEIGHT // 2 + 40)

    # Money particles rising off the title
    if alpha > 0.15:
        title_img = f_title.render(title, True, WHITE)
        tw = title_img.get_width()
        for i in range(18):
            cycle_p = 2.2 + (i % 5) * 0.15
            local = (t * (0.7 + (i % 4) * 0.12) + i * 0.37) % cycle_p
            life = local / cycle_p
            ox = (i / 17.0 - 0.5) * tw * 0.95
            drift = _math.sin(t * 1.4 + i) * 18 * life
            px = WIDTH // 2 + ox + drift
            py = title_y - 8 - life * 90 - (i % 3) * 6
            a = alpha * (1.0 - life) * (1.0 if life > 0.05 else life / 0.05)
            if a <= 0.02:
                continue
            if i % 3 == 0:
                r = max(3, int(7 * (1.0 - life * 0.4)))
                coin = (
                    int(255 * a + BG[0] * (1 - a)),
                    int(210 * a + BG[1] * (1 - a)),
                    int(60 * a + BG[2] * (1 - a)),
                )
                rim = (
                    int(255 * a + BG[0] * (1 - a)),
                    int(240 * a + BG[1] * (1 - a)),
                    int(150 * a + BG[2] * (1 - a)),
                )
                pygame.draw.circle(surface, coin, (int(px), int(py)), r)
                pygame.draw.circle(surface, rim, (int(px), int(py)), max(2, r - 2), 1)
            else:
                labels = ["$", "$", "$$", "+$"]
                lab = labels[i % len(labels)]
                g = (
                    int(ACCENT_GREEN[0] * a + BG[0] * (1 - a)),
                    int(ACCENT_GREEN[1] * a + BG[1] * (1 - a)),
                    int(ACCENT_GREEN[2] * a + BG[2] * (1 - a)),
                )
                sz = max(12, int(16 * (1.0 - life * 0.35)))
                img = get_font(sz, bold=True).render(lab, True, g)
                surface.blit(img, (px - img.get_width() // 2, py - img.get_height() // 2))

    # Loading data cycle (loops with animation)
    data_sources = [
        ("Loading data", "Lucky Orange — returning visitor conversion rates"),
        ("Loading data", "AffiliateBooster — conversion by traffic source"),
        ("Loading data", "EcomHint / Dynamic Yield — ecommerce CVR benchmarks"),
        ("Loading data", "Statista — global conversion rates by industry"),
        ("Loading data", "Stackmatix — website conversion rate benchmarks"),
        ("Loading data", "RepublishAI — content refresh ranking study"),
        ("Loading data", "Workshop Digital — content refresh organic lifts"),
        ("Loading data", "Enterprise Research Centre — SME advisory impact"),
        ("Loading data", "Rule1 / industry email — contact & engagement rates"),
        ("Loading data", "IRP Commerce 2025 — category conversion baselines"),
        ("Loading data", "Calibrating traffic × conversion model…"),
        ("Loading data", "Ready — opening AffiliateStore.com"),
    ]
    idx = int((t * 1.2) % len(data_sources))
    head, detail = data_sources[idx]
    dots = "." * (1 + int((t * 3) % 3))
    blit_c(f"{head}{dots}", f_tag, fade(ACCENT_GREEN), HEIGHT // 2 + 78)
    src_img = f_src.render(detail, True, fade((140, 160, 190)))
    surface.blit(src_img, (WIDTH // 2 - src_img.get_width() // 2, HEIGHT // 2 + 98))

    # Soft progress bar that loops
    bar_w, bar_h = 280, 8
    bx, by = WIDTH // 2 - bar_w // 2, HEIGHT // 2 + 120
    pygame.draw.rect(surface, fade(DARK_GRAY), (bx, by, bar_w, bar_h), border_radius=4)
    fill_w = int(bar_w * phase)
    if fill_w > 0:
        pygame.draw.rect(surface, fade(ACCENT_GREEN), (bx, by, fill_w, bar_h), border_radius=4)

    # Click to continue — below the main panel, animated
    pulse = 0.5 + 0.5 * _math.sin(t * 2.8)
    bob = int(_math.sin(t * 2.2) * 6)
    prompt_col = (
        int(160 + 80 * pulse),
        int(190 + 50 * pulse),
        int(220 + 30 * pulse),
    )
    f_prompt = get_font(20, bold=True)
    prompt = f_prompt.render("Click to continue", True, fade(prompt_col))
    py = panel.bottom + 28 + bob
    px = WIDTH // 2 - prompt.get_width() // 2
    surface.blit(prompt, (px, py))
    # Soft underline
    uw = int(prompt.get_width() * (0.65 + 0.35 * pulse))
    pygame.draw.rect(surface, fade(prompt_col),
                     (WIDTH // 2 - uw // 2, py + prompt.get_height() + 4, uw, 2), border_radius=1)
    # Bouncing chevrons under the prompt
    chev_y = py + prompt.get_height() + 16
    chev_col = fade((
        int(100 + 100 * pulse),
        int(160 + 60 * pulse),
        int(220),
    ))
    for i, ox in enumerate((-18, 0, 18)):
        cy = chev_y + int(_math.sin(t * 3.5 + i * 0.6) * 3)
        cx = WIDTH // 2 + ox
        pygame.draw.lines(surface, chev_col, False,
                          [(cx - 6, cy), (cx, cy + 6), (cx + 6, cy)], 2)


def draw_outro(surface, t):
    """Shutdown sequence — mirror of welcome, systems powering down."""
    surface.fill(BG)
    p = max(0.0, min(1.0, t / OUTRO_DURATION))

    # Fade: full → hold → black
    if p < 0.15:
        alpha = p / 0.15
    elif p < 0.7:
        alpha = 1.0
    else:
        alpha = max(0.0, 1.0 - (p - 0.7) / 0.3)

    def fade(color):
        return (
            int(color[0] * alpha + BG[0] * (1 - alpha)),
            int(color[1] * alpha + BG[1] * (1 - alpha)),
            int(color[2] * alpha + BG[2] * (1 - alpha)),
        )

    import math as _math
    # Grid collapsing inward
    grid = fade((40, 28, 32))
    spacing = 40
    offset = int((-t * 22) % spacing)
    for x in range(-spacing, WIDTH + spacing, spacing):
        pygame.draw.line(surface, grid, (x + offset, 0), (x + offset, HEIGHT), 1)
    for y in range(-spacing, HEIGHT + spacing, spacing):
        pygame.draw.line(surface, grid, (0, y - offset // 2), (WIDTH, y - offset // 2), 1)

    # Nodes disconnecting — radius shrinks over time
    for i in range(12):
        ang = -t * 0.4 + i * (2 * _math.pi / 12)
        rad = max(20, (160 + 40 * _math.sin(t * 0.5 + i)) * (1.0 - p * 0.85))
        nx = WIDTH // 2 + int(_math.cos(ang) * rad)
        ny = HEIGHT // 2 + int(_math.sin(ang) * rad * 0.55)
        r = max(1, 3 + (i % 3) - int(p * 2))
        pygame.draw.circle(surface, fade((180, 70, 80)), (nx, ny), r)
        if p < 0.75:
            pygame.draw.line(surface, fade((90, 40, 50)), (WIDTH // 2, HEIGHT // 2 - 20), (nx, ny), 1)

    panel = pygame.Rect(WIDTH // 2 - 340, HEIGHT // 2 - 130, 680, 280)
    pygame.draw.rect(surface, fade((24, 28, 40)), panel, border_radius=16)
    pygame.draw.rect(surface, fade((180, 80, 90)), panel, 2, border_radius=16)

    f_title = get_font(36, bold=True)
    f_sub = get_font(20)
    f_tag = get_font(15)
    f_src = get_font(13)

    def blit_c(text, font, color, y):
        img = font.render(text, True, fade(color))
        surface.blit(img, (WIDTH // 2 - img.get_width() // 2, y - img.get_height() // 2))

    blit_c("Shutting down", f_title, WHITE, HEIGHT // 2 - 48)
    lw = int(220 * alpha)
    if lw > 8:
        pygame.draw.rect(surface, fade(RED),
                         (WIDTH // 2 - lw // 2, HEIGHT // 2 - 18, lw, 3), border_radius=2)
    blit_c("Affiliate Marketing Simulator", f_sub, (200, 160, 160), HEIGHT // 2 + 8)
    blit_c("By Simon Barnett", f_tag, GRAY, HEIGHT // 2 + 36)

    # Shutdown checklist — reverse of loading data
    steps = [
        ("Closing Smart Catalogue…", "storefront session terminated"),
        ("Flushing traffic models…", "Lucky Orange / AffiliateBooster"),
        ("Archiving conversion logs…", "Statista · Stackmatix · EcomHint"),
        ("Disconnecting partner link…", "consultancy channel closed"),
        ("Saving high scores…", "highscores.json"),
        ("Writing last P&L snapshot…", "last_pnl.json"),
        ("Releasing ad spend buffers…", "promote cooldown cleared"),
        ("Powering down dials…", "traffic · conversion offline"),
        ("Goodbye.", "systems halted"),
    ]
    idx = min(len(steps) - 1, int(p * len(steps)))
    head, detail = steps[idx]
    dots = "." * (1 + int((t * 3) % 3)) if idx < len(steps) - 1 else ""
    blit_c(head + dots, f_tag, fade((255, 160, 160)), HEIGHT // 2 + 70)
    src_img = f_src.render(detail, True, fade((140, 120, 130)))
    surface.blit(src_img, (WIDTH // 2 - src_img.get_width() // 2, HEIGHT // 2 + 92))

    # Progress bar emptying
    bar_w, bar_h = 280, 8
    bx, by = WIDTH // 2 - bar_w // 2, HEIGHT // 2 + 120
    pygame.draw.rect(surface, fade(DARK_GRAY), (bx, by, bar_w, bar_h), border_radius=4)
    fill_w = int(bar_w * (1.0 - p))
    if fill_w > 0:
        pygame.draw.rect(surface, fade((180, 70, 80)), (bx, by, fill_w, bar_h), border_radius=4)

    # Falling $ particles (money leaving)
    if alpha > 0.1:
        for i in range(14):
            cycle = 1.8 + (i % 4) * 0.12
            local = (t * 0.9 + i * 0.4) % cycle
            life = local / cycle
            ox = (i / 13.0 - 0.5) * 320
            px = WIDTH // 2 + ox + _math.sin(t + i) * 12
            py = HEIGHT // 2 - 40 + life * 120
            a = alpha * (1.0 - life * 0.5)
            if a < 0.05:
                continue
            g = (
                int(180 * a + BG[0] * (1 - a)),
                int(80 * a + BG[1] * (1 - a)),
                int(90 * a + BG[2] * (1 - a)),
            )
            img = f_src.render("$", True, g)
            surface.blit(img, (px - img.get_width() // 2, py))


def main():
    try:
        _boot_present("Opening simulator…", 1.0)
    except Exception:
        pass
    # Drop boot/PyInstaller splash — game UI takes over
    _close_boot_splash()

    global has_audience, seo_checked, content_updates, regular_contact, partner_promo, club_site_url
    global intensity, is_holding, promote_lock, max_hold_timer, hold_duration, promote_cooldown, monthly_adspend, hover_help, game_state, day, money
    global is_fullscreen, display, welcome_timer, outro_timer, audio_enabled
    global total_revenue, total_commission, total_costs, total_adspend, total_promote_adspend, total_paidsearch_adspend, sales_count
    global last_sale_timer, last_sale_msg, flash_product_idx, flash_timer, sale_anims
    global hud_anim_t, hud_pulse, hud_display_money, hud_prev_money, hud_sale_flash
    global last_month_charged, scores_recorded_for_run, high_scores, last_gameover_available, flag_anim_t, viewing_historical_pnl, just_finished_loss, last_pnl, years_completed, last_year_net

    day_timer = 0.0
    last_month_charged = 0
    promote_lock = False
    max_hold_timer = 0.0
    hold_duration = 0.0
    monthly_adspend = 0.0

    # Warm up display and replace splash with the real welcome frame
    pygame.event.pump()
    clock.tick(60)
    game_state = STATE_WELCOME
    welcome_timer = 0.0
    _close_boot_splash()
    draw_welcome(canvas, 0.0)
    present()

    running = True
    while running:
        # Cap dt so a long first frame (fullscreen init) cannot skip the whole intro
        dt = min(0.05, clock.tick(60) / 1000.0)
        mouse_pos = map_mouse(pygame.mouse.get_pos())
        hover_help = None

        # Welcome animation loops until the player clicks
        if game_state == STATE_WELCOME:
            welcome_timer += dt
        if game_state == STATE_OUTRO:
            outro_timer += dt
            if outro_timer >= OUTRO_DURATION:
                running = False
        new_game_rect = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game_state != STATE_OUTRO:
                        game_state = STATE_OUTRO
                        outro_timer = 0.0
                    else:
                        running = False  # second Esc skips outro
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and (event.mod & (pygame.KMOD_CTRL | pygame.KMOD_ALT)):
                    # Ctrl+Enter or Alt+Enter toggles fullscreen (letterboxed to keep aspect ratio)
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        display = pygame.display.set_mode((WIDTH, HEIGHT))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = map_mouse(event.pos)
                if game_state == STATE_WELCOME:
                    reset_strategies()
                    reset_game(keep_strategies=False)
                    game_state = STATE_SETUP
                    welcome_timer = 0.0
                    continue

                # Audio toggle (always available)
                if AUDIO_RECT.collidepoint(mx, my):
                    audio_enabled = not audio_enabled

                # Randomise catalogue parts (setup only)
                if game_state == STATE_SETUP and partner_promo and RANDOMISE_RECT.collidepoint(mx, my):
                    randomise_products()
                if game_state == STATE_SETUP and last_gameover_available and FLAG_RECT.collidepoint(mx, my):
                    restore_pnl(historical=True)
                    game_state = STATE_GAMEOVER

                if game_state == STATE_GAMEOVER:
                    # Button FIRST (must not lose to high-score row hits)
                    ng = _gameover_btn_rect or pygame.Rect(
                        WIDTH // 2 - 120, HEIGHT // 2 - 320 + 640 - 56, 240, 44)
                    if ng.collidepoint(mx, my):
                        # Contract lost this run → always return to welcome
                        lost_this_run = bool(
                            _gameover_show_lost
                            or (just_finished_loss and not viewing_historical_pnl)
                        )
                        if lost_this_run:
                            reset_strategies()
                            reset_game(keep_strategies=False)
                            years_completed = 0
                            last_year_net = None
                            viewing_historical_pnl = False
                            just_finished_loss = False
                            welcome_timer = 0.0
                            game_state = STATE_WELCOME  # must be last — reset_game sets SETUP
                        else:
                            # CONTINUE into next year — keep tickboxes
                            reset_game(keep_strategies=True)
                            viewing_historical_pnl = False
                            just_finished_loss = False
                            welcome_timer = 0.0
                            game_state = STATE_SETUP
                    else:
                        # High score rows — recall setup for next year
                        for rect, entry in _hs_click_rects:
                            if rect.collidepoint(mx, my):
                                apply_settings(entry.get("settings", {}))
                                reset_game(keep_strategies=True)
                                apply_settings(entry.get("settings", {}))
                                viewing_historical_pnl = False
                                just_finished_loss = False
                                welcome_timer = 0.0
                                game_state = STATE_SETUP
                                break
                elif game_state == STATE_SETUP:
                    # Tickboxes
                    if pygame.Rect(710, AUDIENCE_Y, 250, 28).collidepoint(mx, my):
                        if partner_promo:
                            has_audience = not has_audience
                            if not has_audience:
                                intensity = 0.0
                                promote_lock = False
                                max_hold_timer = 0.0
                                regular_contact = False
                                content_updates = False
                    if pygame.Rect(710, SEO_Y, 250, 28).collidepoint(mx, my):
                        if partner_promo:
                            seo_checked = not seo_checked
                    if pygame.Rect(710, CONTENT_Y, 250, 28).collidepoint(mx, my):
                        if has_audience:
                            content_updates = not content_updates
                        else:
                            content_updates = False
                    if pygame.Rect(710, CONTACT_Y, 250, 28).collidepoint(mx, my):
                        if has_audience and partner_promo:
                            regular_contact = not regular_contact
                    if pygame.Rect(710, PARTNER_Y, 250, 28).collidepoint(mx, my):
                        partner_promo = not partner_promo
                        if partner_promo:
                            # Partner recommends their customer club site for the catalogue
                            club_site_url = pick_club_site_url()
                        else:
                            club_site_url = None
                            has_audience = False
                            regular_contact = False
                            seo_checked = False
                            content_updates = False
                            intensity = 0.0
                            for s in conversion_strategies:
                                if s["label"] == "Product reviews":
                                    s["checked"] = False
                                if s.get("is_multiplier"):
                                    s["checked"] = False
                    for i, s in enumerate(conversion_strategies):
                        cy = CONV_START_Y + i * CHECK_H
                        if pygame.Rect(990, cy, 250, 28).collidepoint(mx, my):
                            requires_audience = s.get("is_multiplier")
                            requires_partner = s["label"] == "Product reviews"
                            if requires_partner and not partner_promo:
                                pass
                            elif requires_audience and not has_audience:
                                pass
                            else:
                                s["checked"] = not s["checked"]
                    if RANDOMISE_RECT.collidepoint(mx, my):
                        randomise_products()
                    # Start button
                    if START_RECT.collidepoint(mx, my):
                        game_state = STATE_RUNNING
                        hud_anim_t = 0.0
                        hud_pulse = 0.0
                        hud_display_money = 0.0
                        hud_prev_money = 0.0
                        hud_sale_flash = 0.0
                        day = 0
                        money = 0.0
                        total_revenue = 0.0
                        total_commission = 0.0
                        total_costs = 0.0
                        total_adspend = 0.0
                        total_promote_adspend = 0.0
                        total_paidsearch_adspend = 0.0
                        monthly_adspend = 0.0
                        sales_count = 0
                        last_month_charged = 0
                        day_timer = 0.0
                        promote_lock = False
                        max_hold_timer = 0.0
                        monthly_adspend = 0.0
                        scores_recorded_for_run = False

                elif game_state == STATE_RUNNING:
                    if get_quit_rect().collidepoint(mx, my):
                        # End year early — settle accounts then show P&L
                        finalize_year_accounts()
                        record_high_score()
                        snapshot_pnl()
                        game_state = STATE_GAMEOVER

        # Continuous hold: max 1.0s then mandatory 3.0s cooldown.
        # Intensity (promote traffic) ALWAYS decays unless actively holding this frame.
        mouse_pressed = pygame.mouse.get_pressed()[0]
        if game_state == STATE_RUNNING:
            if promote_cooldown > 0:
                promote_cooldown = max(0.0, promote_cooldown - dt)
                promote_lock = True
                is_holding = False
                intensity = max(0.0, intensity - 55.0 * dt)  # fast drop during cooldown
                if promote_cooldown <= 0:
                    promote_lock = False
                    hold_duration = 0.0
                    max_hold_timer = 0.0
            else:
                promote_lock = False
                loss_locked = money < LOSS_PROMOTE_LIMIT
                is_holding = (mouse_pressed and PROMOTE_RECT.collidepoint(mouse_pos)
                              and not loss_locked)
                if is_holding:
                    hold_duration += dt
                    if hold_duration >= 1.0:
                        is_holding = False
                        hold_duration = 0.0
                        promote_cooldown = 3.0
                        promote_lock = True
                        intensity = max(0.0, intensity - 55.0 * dt)
                    else:
                        intensity = min(100.0, intensity + 50.0 * dt)
                else:
                    hold_duration = 0.0
                    max_hold_timer = 0.0
                    intensity = max(0.0, intensity - 45.0 * dt)  # clear drop on release
        else:
            is_holding = False
            intensity = max(0.0, intensity - 45.0 * dt)
            promote_lock = False
            max_hold_timer = 0.0

        if not partner_promo:
            has_audience = False
        if not has_audience:
            regular_contact = False  # can't contact without an audience
            for s in conversion_strategies:
                if s.get("is_multiplier"):
                    s["checked"] = False
        if not partner_promo:
            regular_contact = False  # club needs partner for regular contact
            seo_checked = False      # SEO needs partner
            for s in conversion_strategies:
                if s["label"] == "Product reviews":
                    s["checked"] = False

        # Time progression — advance ONE day at a time (6 days per real second)
        if game_state == STATE_RUNNING:
            day_timer += dt * 6.0   # accumulate game-days
            while day_timer >= 1.0 and game_state == STATE_RUNNING:
                day_timer -= 1.0
                day += 1
                # Community ends contract early if loss exceeds $1,000
                if money < EARLY_CONTRACT_LOSS:
                    finalize_year_accounts()
                    record_high_score()
                    snapshot_pnl(force_reason="early_loss")
                    game_state = STATE_GAMEOVER
                    break
                # Always-on paid search (industry-modest daily budget) — independent of promote
                paid_search_on = any(s["label"] == "Paid search" and s["checked"] for s in conversion_strategies)
                if paid_search_on:
                    remaining = max(0.0, ADSPEND_HARD_CAP - monthly_adspend)
                    daily = PAID_SEARCH_DAILY * (0.75 if partner_promo else 1.0)
                    ps_spend = min(daily, remaining)
                    if ps_spend > 0:
                        money -= ps_spend
                        total_adspend += ps_spend
                        total_paidsearch_adspend += ps_spend
                        total_costs += ps_spend
                        monthly_adspend += ps_spend

                # Promote ALWAYS costs. To partner only when engaging own members (audience); else external.
                # With SEO or paid-search links active, promote costs 2x (competing auction / denser bidding).
                if intensity > 1.0:
                    visitors = intensity * VISITORS_PER_INTENSITY
                    if has_audience:
                        cpc = AUDIENCE_CPC
                    else:
                        cpc = CPC_BASE
                    if partner_promo:
                        cpc *= 0.65  # better creative still helps efficiency
                    # 2x promote cost when SEO and/or paid search links are in play
                    if seo_checked or paid_search_on:
                        cpc *= 2.0
                    spend = visitors * cpc
                    if has_audience:
                        remaining = max(0.0, min(ADSPEND_MONTHLY_CAP, ADSPEND_HARD_CAP) - monthly_adspend)
                    else:
                        remaining = max(0.0, ADSPEND_HARD_CAP - monthly_adspend)
                    spend = min(spend, remaining)
                    if has_audience and remaining > 0 and spend < 0.05:
                        spend = min(0.05, remaining)
                    if spend > 0:
                        money -= spend
                        total_adspend += spend
                        total_promote_adspend += spend
                        total_costs += spend
                        monthly_adspend += spend
                try_auto_sale()
                m = current_month()
                if m > last_month_charged and m <= 12:
                    if partner_promo:
                        money -= MONTHLY_COST
                        total_costs += MONTHLY_COST
                    last_month_charged = m
                    monthly_adspend = 0.0  # reset monthly AdSpend caps
                # After all daily costs: early contract end if loss > $1,000
                if money < EARLY_CONTRACT_LOSS:
                    finalize_year_accounts()
                    record_high_score()
                    snapshot_pnl(force_reason="early_loss")
                    game_state = STATE_GAMEOVER
                    break
                if day >= TOTAL_DAYS:
                    finalize_year_accounts()
                    record_high_score()
                    snapshot_pnl()
                    game_state = STATE_GAMEOVER
                    break

        flag_anim_t += dt
        if last_sale_timer > 0:
            last_sale_timer -= dt
        if flash_timer > 0:
            flash_timer -= dt
            if flash_timer <= 0:
                flash_product_idx = -1
        # Animate purchase icons
        for anim in sale_anims[:]:
            anim["t"] += dt
            anim["y"] += anim["vy"] * dt
            if anim["t"] >= anim["life"]:
                sale_anims.remove(anim)

        # HUD animations
        if game_state == STATE_RUNNING:
            hud_anim_t = min(1.0, hud_anim_t + dt * 2.2)  # ~0.45s entrance
            # Smooth money count-up/down
            diff = money - hud_display_money
            hud_display_money += diff * min(1.0, dt * 8.0)
            if abs(diff) < 0.5:
                hud_display_money = money
            # Pulse when money changes meaningfully
            if abs(money - hud_prev_money) > 0.5:
                hud_pulse = 1.0
                if money > hud_prev_money:
                    hud_sale_flash = 1.0
                hud_prev_money = money
            hud_pulse = max(0.0, hud_pulse - dt * 2.5)
            hud_sale_flash = max(0.0, hud_sale_flash - dt * 2.0)
        else:
            hud_anim_t = 0.0

        traffic = get_traffic()
        conversion = get_conversion()
        commission_proxy = get_commission_proxy()
        tint = monitor_tint()

        # Hover
        if game_state != STATE_GAMEOVER:
            if pygame.Rect(710, PARTNER_Y, 250, 28).collidepoint(mouse_pos):
                hover_help = TRAFFIC_HELP["partner"]
            elif pygame.Rect(710, AUDIENCE_Y, 250, 28).collidepoint(mouse_pos):
                lr = lock_reason_for_traffic("audience")
                hover_help = lr if lr else TRAFFIC_HELP["audience"]
            elif pygame.Rect(710, SEO_Y, 250, 28).collidepoint(mouse_pos):
                lr = lock_reason_for_traffic("seo")
                hover_help = lr if lr else TRAFFIC_HELP["seo"]
            elif pygame.Rect(710, CONTACT_Y, 250, 28).collidepoint(mouse_pos):
                lr = lock_reason_for_traffic("contact")
                hover_help = lr if lr else TRAFFIC_HELP["contact"]
            elif pygame.Rect(710, CONTENT_Y, 250, 28).collidepoint(mouse_pos):
                lr = lock_reason_for_traffic("content")
                hover_help = lr if lr else TRAFFIC_HELP["content"]
            elif RANDOMISE_RECT.collidepoint(mouse_pos) and game_state == STATE_SETUP:
                hover_help = "Shuffle the catalogue with 6 new products and prices."
            elif RANDOMISE_RECT.collidepoint(mouse_pos):
                hover_help = "Catalogue is locked for the year — randomise only in setup."
            elif PROMOTE_RECT.collidepoint(mouse_pos):
                if game_state == STATE_RUNNING and money < LOSS_PROMOTE_LIMIT:
                    hover_help = ("Promote blocked: the club is more than $100 in the red and will not "
                                  "pay to lose more money on ads. Grow sales or cut costs first.")
                elif game_state != STATE_RUNNING:
                    hover_help = "Available after START YEAR — lock strategies and begin."
                else:
                    hover_help = ("What: hold to promote (max 1s, then 3s cooldown) — a short traffic push. "
                                  "Money: to the partner only when Has an Audience (engaging members); otherwise paid externally. "
                                  "Buying cold traffic costs more than engaging members. Costs 2× while SEO or Paid search is on. "
                                  "Blocked if the community is over $100 in the red.")
            else:
                for i, s in enumerate(conversion_strategies):
                    cy = CONV_START_Y + i * CHECK_H
                    if pygame.Rect(990, cy, 250, 28).collidepoint(mouse_pos):
                        lr = lock_reason_for_conversion(s)
                        hover_help = lr if lr else s["help"]
                        break

        # ---- DRAW ----
        if game_state == STATE_WELCOME:
            draw_welcome(screen, welcome_timer)
            present()
            continue
        if game_state == STATE_OUTRO:
            draw_outro(screen, outro_timer)
            present()
            continue

        screen.fill(BG)
        draw_monitor_frame(screen)
        draw_browser_catalogue(screen, tint)
        # Floating purchase icons
        for anim in sale_anims:
            p = anim["t"] / anim["life"]
            alpha = 1.0 - p
            # coin circle
            r = max(4, int(12 * (1.0 - p * 0.3)))
            col = (
                int(255 * alpha + BG[0] * (1 - alpha)),
                int(215 * alpha + BG[1] * (1 - alpha)),
                int(60 * alpha + BG[2] * (1 - alpha)),
            )
            pygame.draw.circle(screen, col, (int(anim["x"]), int(anim["y"])), r)
            pygame.draw.circle(screen, (255, 255, 200), (int(anim["x"]), int(anim["y"])), max(2, r - 3), 1)
            tcol = (
                int(ACCENT_GREEN[0] * alpha + BG[0] * (1 - alpha)),
                int(ACCENT_GREEN[1] * alpha + BG[1] * (1 - alpha)),
                int(ACCENT_GREEN[2] * alpha + BG[2] * (1 - alpha)),
            )
            st = font_small.render(anim["text"], True, tcol)
            screen.blit(st, (anim["x"] - st.get_width() // 2, anim["y"] - 22))
        if game_state != STATE_GAMEOVER:
            if game_state == STATE_SETUP and partner_promo:
                draw_randomise_button(screen, enabled=True)
        draw_rounded_rect(screen, PANEL_BG, RIGHT_PANEL, radius=12)

        # TRAFFIC COLUMN
        draw_rounded_rect(screen, COLUMN_BG, TRAFFIC_COL, radius=10)
        hdr = font_header.render("TRAFFIC", True, ACCENT_BLUE)
        screen.blit(hdr, (TRAFFIC_COL.centerx - hdr.get_width() // 2, 50))

        # Zero mark = 2k (audience) or 0 (cold). Needle is excess above that minimum.
        potential = get_traffic_potential()
        if has_audience:
            traffic_dial = max(0.0, potential - 25.0)
            traffic_max = 75.0
            zero_lbl = "2k"
        else:
            traffic_dial = potential
            traffic_max = 100.0
            zero_lbl = "0"
        draw_knob(screen, TRAFFIC_KNOB, KNOB_R, traffic_dial, traffic_max, "TRAFFIC", ACCENT_BLUE, zero_label=zero_lbl)
        draw_strategy_heading(screen, TRAFFIC_COL, "Traffic Strategy", ACCENT_BLUE, "traffic", flag_anim_t)

        can_edit = (game_state == STATE_SETUP)
        draw_checkbox(screen, 710, PARTNER_Y, partner_promo, "Partner Promotion", enabled=can_edit)
        draw_checkbox(screen, 710, AUDIENCE_Y, has_audience, "Has an Audience (min 2k)",
                      enabled=can_edit and partner_promo)
        draw_checkbox(screen, 710, SEO_Y, seo_checked, "SEO optimized content",
                      enabled=can_edit and not has_audience and partner_promo)
        draw_checkbox(screen, 710, CONTACT_Y, regular_contact, "Regular Contact",
                      enabled=can_edit and has_audience and partner_promo)
        draw_checkbox(screen, 710, CONTENT_Y, content_updates, "Regular content updates",
                      enabled=can_edit and has_audience)

        loss_locked = (game_state == STATE_RUNNING and money < LOSS_PROMOTE_LIMIT)
        draw_hold_button(screen, is_holding, enabled=(game_state == STATE_RUNNING),
                         locked=promote_lock, cooldown=promote_cooldown, loss_locked=loss_locked)

        # CONVERSION COLUMN
        draw_rounded_rect(screen, COLUMN_BG, CONV_COL, radius=10)
        hdr2 = font_header.render("CONVERSION", True, ACCENT_ORANGE)
        screen.blit(hdr2, (CONV_COL.centerx - hdr2.get_width() // 2, 50))
        draw_knob(screen, CONV_KNOB, KNOB_R, max(0.0, conversion - 1.0), 7.0, "CONVERSION", ACCENT_ORANGE, zero_label="1%")
        draw_strategy_heading(screen, CONV_COL, "Conversion Strategy", ACCENT_ORANGE, "conversion", flag_anim_t)

        for i, s in enumerate(conversion_strategies):
            cy = CONV_START_Y + i * CHECK_H
            requires_audience = s.get("is_multiplier")
            requires_partner = s["label"] == "Product reviews"
            if requires_partner:
                enabled = can_edit and partner_promo
            elif requires_audience:
                enabled = can_edit and has_audience
            else:
                enabled = can_edit
            draw_checkbox(screen, 990, cy, s["checked"], s["label"], enabled=enabled)

        if game_state == STATE_SETUP:
            draw_start_button(screen)
            draw_flag_button(screen, flag_anim_t)
        elif game_state == STATE_RUNNING:
            # Animated HUD panel
            import math as _m
            base_rect = get_hud_rect()
            # Entrance: slide up + fade
            ease = 1.0 - (1.0 - hud_anim_t) ** 3  # ease-out cubic
            slide = int((1.0 - ease) * 28)
            alpha = int(215 * ease)
            hud_rect = base_rect.move(0, slide)

            hud_surf = pygame.Surface((hud_rect.w, hud_rect.h), pygame.SRCALPHA)
            hud_surf.fill((18, 22, 34, max(0, alpha)))
            screen.blit(hud_surf, hud_rect.topleft)

            # Border: blue, green pulse on gain, red-ish on loss pulse
            br, bg, bb = 70, 130, 200
            if hud_sale_flash > 0:
                br = int(70 + 50 * hud_sale_flash)
                bg = int(130 + 80 * hud_sale_flash)
                bb = int(200 - 40 * hud_sale_flash)
            elif hud_pulse > 0 and money < 0:
                br = int(70 + 100 * hud_pulse)
                bg = int(130 - 80 * hud_pulse)
                bb = int(200 - 100 * hud_pulse)
            border_w = 2 + (1 if hud_pulse > 0.3 else 0)
            pygame.draw.rect(screen, (br, bg, bb), hud_rect, border_w, border_radius=10)

            # Soft top highlight scanline
            if ease > 0.5:
                scan_y = hud_rect.y + 4 + int((_m.sin(pygame.time.get_ticks() * 0.003) * 0.5 + 0.5) * (hud_rect.h - 50))
                scan = pygame.Surface((hud_rect.w - 8, 2), pygame.SRCALPHA)
                scan.fill((100, 160, 255, 30))
                screen.blit(scan, (hud_rect.x + 4, scan_y))

            # --- Compact header: calendar icon + date (sales-sized) · balance ---
            # Mini calendar icon
            ix, iy = hud_rect.x + 10, hud_rect.y + 5
            cal = pygame.Rect(ix, iy, 14, 14)
            pygame.draw.rect(screen, (70, 100, 150), cal, border_radius=2)
            pygame.draw.rect(screen, (140, 180, 230), cal, 1, border_radius=2)
            pygame.draw.rect(screen, (50, 70, 110), (ix, iy, 14, 4), border_radius=1)
            for dx in (3, 7, 11):
                pygame.draw.line(screen, (200, 220, 255), (ix + dx, iy + 1), (ix + dx, iy + 3), 1)
            # day dots
            pygame.draw.rect(screen, (180, 200, 230), (ix + 2, iy + 6, 3, 2))
            pygame.draw.rect(screen, (180, 200, 230), (ix + 6, iy + 6, 3, 2))
            pygame.draw.rect(screen, (180, 200, 230), (ix + 10, iy + 6, 2, 2))
            pygame.draw.rect(screen, (180, 200, 230), (ix + 2, iy + 10, 3, 2))
            pygame.draw.rect(screen, (180, 200, 230), (ix + 6, iy + 10, 3, 2))

            date_txt = font_small.render(current_date_str(), True, WHITE)
            screen.blit(date_txt, (ix + 18, hud_rect.y + 5))
            disp = hud_display_money
            money_col = ACCENT_GREEN if disp >= 0 else RED
            money_txt = font_med_bold.render(f"${disp:,.0f}", True, money_col)
            screen.blit(money_txt, (hud_rect.right - money_txt.get_width() - 10, hud_rect.y + 4))
            pygame.draw.line(screen, (45, 55, 75),
                             (hud_rect.x + 8, hud_rect.y + 24),
                             (hud_rect.right - 8, hud_rect.y + 24), 1)

            partner_fees = max(0.0, total_costs - total_adspend)
            plat_c = total_commission * 0.50
            part_c = total_commission * 0.25
            comm_c = total_commission * 0.25
            hud_adspend = total_adspend + partner_fees  # promote + paid search + engagement
            promote_spent = float(total_promote_adspend)
            paid_spent = float(total_paidsearch_adspend)

            mid = hud_rect.x + hud_rect.w // 2
            y0 = hud_rect.y + 28
            hud_hovers = []  # (rect, help)

            def cell(x, y, w, label, val, col, tip):
                screen.blit(font_tiny.render(label, True, GRAY), (x, y))
                vt = font_tiny.render(val, True, col)
                screen.blit(vt, (x + w - vt.get_width(), y))
                hud_hovers.append((pygame.Rect(x - 2, y - 1, w + 4, 14), tip))

            cell(hud_rect.x + 10, y0, 100, "Sales", f"{sales_count:,}", WHITE,
                 "Sales: number of catalogue purchases completed so far this year. "
                 "Each sale is rolled from traffic × conversion% each game-day "
                 "(visitors ≈ traffic dial / 100 × 40; buy chance = conversion / 100).")
            cell(mid, y0, 100, "Gross", f"${total_revenue:,.0f}", GRAY,
                 "Gross sales value: sum of product retail prices for every completed sale. "
                 "Not commission — full catalogue price before the affiliate rate is applied.")
            # Single AdSpend line (promote + paid search + $20/mo partner engagement)
            cell(hud_rect.x + 10, y0 + 14, hud_rect.w - 28, "AdSpend", f"${hud_adspend:,.0f}", (255, 150, 90),
                 "AdSpend — all community marketing outlay: "
                 f"promote ${promote_spent:,.0f} (external; 2× while SEO or Paid search is on) + "
                 f"paid search ${paid_spent:,.0f} + partner engagement ${partner_fees:,.0f} "
                 "($20/mo while Partner Promotion is on). "
                 "AdSpend total = promote + paid search + $20/mo partner retainer. Promote → partner only when engaging own members; otherwise external. Paid search → always Google. Retainer → always partner.")

            # Commission strip
            cy = y0 + 32
            screen.blit(font_tiny.render("COMMISSION", True, ACCENT_ORANGE), (hud_rect.x + 10, cy))
            hud_hovers.append((
                pygame.Rect(hud_rect.x + 8, cy - 1, 90, 12),
                "Commission section: gross affiliate earnings from sales, then split "
                "Platform 50% / Partner 25% / Community 25%. "
                "Per sale: price × product rate (10–30%) × capture rate "
                "(~65–100% with audience / club-benefit framing)."
            ))
            cy += 13
            cols = [
                ("Gross", f"${total_commission:,.0f}", ACCENT_GREEN,
                 "Gross commission: sum over sales of (price × product commission rate × capture). "
                 "Product rates are random 10–30%. Capture is ~90% cold, ~65% audience without "
                 "'My club get the commission', 100% when club-benefit is on."),
                ("Platform", f"${plat_c:,.0f}", (140, 180, 220),
                 "Platform share: 50% of gross commission. "
                 f"Calculation: ${total_commission:,.0f} × 0.50 = ${plat_c:,.0f}. "
                 "Not reduced by AdSpend — the platform is paid off the top."),
                ("Partner", f"${part_c:,.0f}", (180, 160, 255),
                 "Partner commission share: 25% of gross commission only (not the engagement fee). "
                 f"Calculation: ${total_commission:,.0f} × 0.25 = ${part_c:,.0f}. "
                 "On the P&L the partner also receives the $20/mo fee and any paid-search burn routed through them."),
                ("Community", f"${comm_c:,.0f}", (120, 220, 160),
                 "Community commission share: 25% of gross before costs. "
                 f"Calculation: ${total_commission:,.0f} × 0.25 = ${comm_c:,.0f}. "
                 "Running balance (top-right) is this share minus promote, paid search, and engagement fees."),
            ]
            cw = (hud_rect.w - 20) // 4
            for i, (lab, val, col, tip) in enumerate(cols):
                cx = hud_rect.x + 10 + i * cw
                screen.blit(font_tiny.render(lab, True, GRAY), (cx, cy))
                screen.blit(font_tiny.render(val, True, col), (cx, cy + 12))
                hud_hovers.append((pygame.Rect(cx - 2, cy - 1, cw, 28), tip))

            qrect = get_quit_rect().move(0, slide)
            draw_quit_button(screen, qrect)
            hud_hovers.append((
                qrect,
                "Quit year: stops the calendar, projects remaining days from current traffic × conversion, "
                "then opens the year-end P&L. Community share is what contract rules use."
            ))

            # Date / balance hover
            hud_hovers.append((
                pygame.Rect(hud_rect.x + 8, hud_rect.y + 2, 120, 20),
                "Date: simulated calendar (Jan 1 → Dec 25). 1 real second ≈ 6 game-days. "
                "Sales and costs accrue each game-day while the year is running."
            ))
            hud_hovers.append((
                pygame.Rect(hud_rect.right - 110, hud_rect.y + 2, 100, 20),
                "Community balance: running community share of commission minus all community costs. "
                "Calculation: Σ(sale commission × 25%) − promote − paid search − $20/mo engagement. "
                "This is what year-over-year and under-$600 rules judge."
            ))

            for rect, tip in hud_hovers:
                if rect.collidepoint(mouse_pos):
                    hover_help = tip
                    break

            if not partner_promo and BROWSER_RECT.collidepoint(mouse_pos):
                hover_help = ("What: no club website is available yet. "
                              "Needs: Partner Promotion — the partner recommends a club customer "
                              "and logs in to place Smart Catalogue on that club's page "
                              "(e.g. bristolrugbyclub.com). "
                              "You have no website of your own to host the catalogue.")
            if last_sale_timer > 0:
                sc = ACCENT_GREEN if "SOLD" in last_sale_msg else GRAY
                st = font_small.render(last_sale_msg, True, sc)
                screen.blit(st, (BROWSER_RECT.centerx - st.get_width() // 2, BROWSER_RECT.bottom - 22))

        draw_equation(screen, intensity, conversion, commission_proxy, holding=is_holding)

        draw_audio_button(screen)
        footer = font_tiny.render(
            "10–30% commission  •  Partner $20/mo  •  1s≈6 days  •  Ctrl/Alt+Enter fullscreen  •  Esc quit",
            True, GRAY
        )
        screen.blit(footer, (WIDTH // 2 - footer.get_width() // 2, HEIGHT - 28))

        if game_state == STATE_GAMEOVER:
            new_game_rect = draw_game_over(screen)
            # P&L row rollovers
            for rect, tip in _pnl_hover_rects:
                if rect.collidepoint(mouse_pos):
                    hover_help = tip
                    break

        if hover_help:
            if PROMOTE_RECT.collidepoint(mouse_pos):
                draw_tooltip(screen, hover_help, mouse_pos,
                             anchor_rect=PROMOTE_RECT, prefer_below=True)
            else:
                draw_tooltip(screen, hover_help, mouse_pos)

        present()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
