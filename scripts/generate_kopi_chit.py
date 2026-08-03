"""Render the order chit: what a year of this account actually says.

Pure by contract. Everything drawn here is a function of the stats dict handed
in, which is why the committed asset can still be compared byte for byte
against a fresh render even though the numbers change daily. Nothing in this
module touches the network.

The card leads with a finding, not a total. A total and a streak are the same
numbers GitHub prints directly above this image, so the hero is the derived
one: how much of the year landed in its ten busiest days.

Shapes tried and thrown out, each recorded in the design doc: a second detailed
glass repeated the signboard, a calendar of small squares was GitHub's own
graphic in a warmer palette, twelve monthly cup rings were mostly empty, and
seven glasses turned the card into a dashboard of small multiples.
"""

from datetime import date, timedelta
from math import cos, radians, sin
from pathlib import Path
from string import Template
from xml.sax.saxutils import escape
import json

from generate_kopi_sign import PALETTES, to_ascii_entities

CHIT_TOKENS = {
    "dark": {"g0": "#2A2119"},
    "light": {"g0": "#E6D8C0"},
}

BORROWED = ("paper", "panel", "ink", "ink_soft", "accent", "rule")

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"
STATS_FILE = ROOT / "data" / "stats.json"

WIDTH, HEIGHT = 900, 440

# Nested enclosures: the outer sheet holds the chit, which sits inset with its
# own hairline. A card laid flat on one background reads as a screenshot.
SHEET_R = 26
CHIT_LEFT, CHIT_RIGHT = 24, 876
CHIT_TOP, CHIT_BOTTOM = 22, 400
TEETH, TOOTH_DROP = 68, 14

PAD_L, PAD_R = 62, 838

PILL_X, PILL_Y, PILL_W, PILL_H = 62, 80, 168.0, 22.0

# Left column: a radial gauge carrying the hero finding.
RING_CX, RING_CY, RING_R, RING_W = 196.0, 186.0, 68.0, 13.0

# Right column: the last thirty days as an area chart. Dense where a per month
# or per year view is mostly empty, and it visibly moves every morning.
SPARK_L, SPARK_R = 380.0, 838.0
SPARK_BASE, SPARK_H = 200.0, 78.0
SPARK_DAYS = 30
FIGURE_Y = 246

# One strip split into seven segments by share of the week. Seven separate
# glasses were tried and dropped: small multiples turn a card into a dashboard,
# and most of each glass was empty outline. A single proportional bar shows the
# same lopsidedness in one line, and a near dead Friday reads as the sliver it
# actually is.
STRIP_TOP, STRIP_H = 330.0, 22.0
STRIP_GAP, STRIP_MIN = 4.0, 2.0
DOW_LABEL_Y = 368
DOW_TAG_Y = 384

BURST_DAYS = 10

# A burst share needs real volume behind it before it is worth a headline.
BURST_FLOOR = 150

MONTHS = (
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
)
WEEKDAYS = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
INITIALS = ("M", "T", "W", "T", "F", "S", "S")

STYLE = """
    text { font-family: Georgia, "Iowan Old Style", "Palatino Linotype", "Times New Roman", serif; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
    .ink { fill: $ink; }
    .soft { fill: $ink_soft; }
    .sheet { fill: $paper; }
    .chit { fill: $panel; stroke: $rule; stroke-width: 1.25; }
    .dot { fill: none; stroke: $rule; stroke-width: 1; stroke-dasharray: 1 3; }
    .pill { fill: none; stroke: $rule; stroke-width: 1; }
    .meta { font-size: 9px; letter-spacing: 1.8px; }
    .eyebrow { font-size: 8px; letter-spacing: 2.4px; }
    .hero { font-size: 40px; font-weight: 700; letter-spacing: -1px; fill: $accent; }
    .figure { font-size: 26px; font-weight: 700; letter-spacing: -0.4px; }
    .ring-track { fill: none; stroke: $g0; stroke-width: 13; }
    .ring { fill: none; stroke: $accent; stroke-width: 13; stroke-linecap: round; }
    .spark-fill { fill: $accent; opacity: 0.16; }
    .spark-line { fill: none; stroke: $accent; stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
    .spark-base { fill: none; stroke: $rule; stroke-width: 1; }
    .spark-dot { fill: $accent; }
    .caption { font-size: 12px; letter-spacing: 0.3px; }
    .day { font-size: 9px; letter-spacing: 2px; }
    .tag { font-size: 8px; letter-spacing: 1.6px; fill: $accent; }
    .seg { fill: $accent; }
    .seg-quiet { fill: $g0; }
    /* Only the rest day tag moves, and it rests at full opacity, so a renderer
       parked at t=0 shows the finished card. An earlier version animated the
       artwork itself and rendered wrong wherever the animation was not
       running. */
    .blink { animation: settle 3.4s ease-in-out infinite; }
    @keyframes settle {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.45; }
    }
    @media (prefers-reduced-motion: reduce) {
      .still { animation: none !important; }
    }
"""


def palette(theme):
    """Only what the chit actually paints with, so a dead token is a failure."""
    borrowed = {key: PALETTES[theme][key] for key in BORROWED}
    return {**borrowed, **CHIT_TOKENS[theme]}


def num(value):
    """Trim float noise so the asset is byte stable across platforms."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


def count(value):
    return f"{value:,}"


def days_label(value):
    return f"{value} day" if value == 1 else f"{value} days"


def stamp(iso):
    """Format without strftime, which would drag in the runner's locale."""
    day = date.fromisoformat(iso)
    return f"{day.day:02d} {MONTHS[day.month - 1]} {day.year}"


def short_stamp(day):
    return f"{day.day:02d} {MONTHS[day.month - 1]}"


def each_day(stats):
    daily = stats.get("daily") or []
    if not daily or not stats.get("window_start"):
        return []
    start = date.fromisoformat(stats["window_start"])
    return [(start + timedelta(days=offset), value) for offset, value in enumerate(daily)]


def weekday_totals(stats):
    """Monday first, matching the letters printed under the strip."""
    totals = [0] * 7
    for day, value in each_day(stats):
        totals[day.weekday()] += value
    return totals


def rest_day(stats):
    """The weekday this account is effectively shut.

    Only claimed when the quietest weekday is genuinely far below the average,
    otherwise an evenly spread week would get an arbitrary day labelled.
    """
    totals = weekday_totals(stats)
    if sum(totals) <= 0:
        return None
    quietest = min(range(7), key=lambda index: totals[index])
    return quietest if totals[quietest] * 3 < sum(totals) / 7 else None


def burst_share(stats, top=BURST_DAYS):
    """How much of the year landed in its busiest handful of days."""
    daily = sorted(stats.get("daily") or [], reverse=True)
    total = sum(daily)
    if total <= 0:
        return 0.0
    return sum(daily[:top]) / total


def best_run_end(stats):
    """The day the longest unbroken run finished, so the streak has a date."""
    best = run = 0
    end = None
    for day, value in each_day(stats):
        run = run + 1 if value > 0 else 0
        if run > best:
            best, end = run, day
    return end


def streak_label(stats):
    end = best_run_end(stats)
    return f"LONGEST STREAK, TO {short_stamp(end)}" if end else "LONGEST STREAK"


def strength(value, floor, ceiling):
    """Zero until a finding is worth saying, then rising to one.

    Below the floor a finding is not interesting: a 19% burst share or a four
    day streak is just noise, and promoting it would give the card a headline
    that means nothing.
    """
    if value <= floor:
        return 0.0
    return min(1.0, (value - floor) / (ceiling - floor))


# Which supporting figures to fall back on, in order, once the hero is taken.
SUPPORT_ORDER = ("total", "streak", "steady", "running", "burst")


def candidates(stats):
    """Every headline this card could lead with, scored against each other.

    Hardcoding one finding does not survive a change of habit. A burst share is
    a striking headline at 57% and an embarrassing one at 19%, and the same is
    true in reverse for a consistency stat. Scoring means the card always leads
    with whatever is currently true and worth reading, and quietly demotes a
    finding once it stops being remarkable. The last entry scores zero on
    purpose: it is the floor, so there is always something to print.
    """
    total = stats.get("total_contributions", 0)
    days_total = stats.get("days_total") or 0
    active = stats.get("days_active", 0)
    run = stats.get("longest_run", 0)
    running = stats.get("current_run", 0)
    share = burst_share(stats)
    ratio = active / days_total if days_total else 0.0
    end = best_run_end(stats)

    return [
        {
            "key": "total",
            "score": 0.0,
            "value": count(total),
            "eyebrow": "COMMITS, PAST YEAR",
            "caption": f"pushed over the last {days_total} days",
            "figure": count(total),
            "label": "COMMITS, PAST YEAR",
            "gauge": min(1.0, active / days_total) if days_total else 0.0,
        },
        {
            "key": "burst",
            "score": strength(share, 0.35, 0.9) if total >= BURST_FLOOR else 0.0,
            "value": f"{share:.0%}",
            "eyebrow": f"BUSIEST {BURST_DAYS} DAYS",
            "caption": f"of the whole year landed in {BURST_DAYS} days",
            "figure": f"{share:.0%}",
            "label": f"IN THE BUSIEST {BURST_DAYS} DAYS",
            "gauge": share,
        },
        {
            "key": "steady",
            "score": strength(ratio, 0.45, 0.95),
            "value": f"{ratio:.0%}",
            "eyebrow": "DAYS WORKED",
            "caption": "of the year had something pushed to it",
            "figure": f"{active}/{days_total}",
            "label": "DAYS WORKED",
            "gauge": ratio,
        },
        {
            "key": "running",
            "score": strength(running, 9, 45),
            "value": str(running),
            "eyebrow": "ON A RUN",
            "caption": "days in a row, and still going",
            "figure": days_label(running),
            "label": "CURRENT RUN",
            "gauge": min(1.0, running / 60),
        },
        {
            "key": "streak",
            "score": strength(run, 13, 60),
            "value": str(run),
            "eyebrow": "LONGEST STREAK",
            "caption": (
                f"days in a row, ending {short_stamp(end)}" if end else "days in a row"
            ),
            "figure": days_label(run),
            "label": streak_label(stats),
            "gauge": min(1.0, run / 60),
        },
    ]


def hero_and_support(stats):
    """The strongest finding leads. Two others fill the right hand column.

    max() keeps the first of any tie, and the candidate list is a fixed order,
    so the choice is deterministic and the asset stays byte reproducible.
    """
    pool = {entry["key"]: entry for entry in candidates(stats)}
    hero = max(pool.values(), key=lambda entry: entry["score"])
    support = [pool[key] for key in SUPPORT_ORDER if key != hero["key"]][:2]
    return hero, support


def week_segments(stats):
    """Widths proportional to each weekday's share of the whole week.

    Proportional widths are what make the point: a near dead Friday comes out
    as the sliver it is, next to a Sunday taking a quarter of the strip.
    """
    totals = weekday_totals(stats)
    span = PAD_R - PAD_L - 6 * STRIP_GAP
    whole = sum(totals)
    if whole <= 0:
        share = [1 / 7] * 7
    else:
        share = [value / whole for value in totals]
    widths = [max(STRIP_MIN, part * span) for part in share]
    out, x = [], float(PAD_L)
    for index, width in enumerate(widths):
        out.append((x, width))
        x += width + STRIP_GAP
    return out


def week_strip(stats):
    quiet = rest_day(stats)
    rows = []
    for index, (x, width) in enumerate(week_segments(stats)):
        style = "seg-quiet" if index == quiet else "seg"
        centre = x + width / 2
        rows.append(
            f'  <rect class="{style}" x="{num(x)}" y="{num(STRIP_TOP)}" '
            f'width="{num(width)}" height="{num(STRIP_H)}" rx="3"/>'
        )
        rows.append(
            f'  <text x="{num(centre)}" y="{DOW_LABEL_Y}" text-anchor="middle" '
            f'class="soft mono day">{INITIALS[index]}</text>'
        )
        if index == quiet:
            rows.append(
                f'  <text x="{num(centre)}" y="{DOW_TAG_Y}" text-anchor="middle" '
                f'class="tag mono blink still">closed</text>'
            )
    return "\n".join(rows)


def ring_arc(fraction):
    """A gauge sweep from twelve o'clock, clockwise.

    Capped just short of a full turn because an arc whose start and end points
    coincide is degenerate and renders as nothing at all.
    """
    sweep = min(359.9, max(0.0, fraction) * 360.0)
    start, end = radians(-90.0), radians(-90.0 + sweep)
    x1 = RING_CX + RING_R * cos(start)
    y1 = RING_CY + RING_R * sin(start)
    x2 = RING_CX + RING_R * cos(end)
    y2 = RING_CY + RING_R * sin(end)
    large = 1 if sweep > 180 else 0
    return f"M {num(x1)} {num(y1)} A {num(RING_R)} {num(RING_R)} 0 {large} 1 {num(x2)} {num(y2)}"


def recent(stats):
    """The last thirty days, oldest first, padded if the history is shorter."""
    tail = (stats.get("daily") or [])[-SPARK_DAYS:]
    return [0] * (SPARK_DAYS - len(tail)) + tail


def spark_points(stats):
    counts = recent(stats)
    peak = max(counts) or 1
    step = (SPARK_R - SPARK_L) / (len(counts) - 1)
    return [
        (SPARK_L + index * step, SPARK_BASE - (value / peak) * SPARK_H)
        for index, value in enumerate(counts)
    ]


def spark(stats):
    points = spark_points(stats)
    line = " ".join(f"{num(x)},{num(y)}" for x, y in points)
    area = f"{num(SPARK_L)},{num(SPARK_BASE)} {line} {num(SPARK_R)},{num(SPARK_BASE)}"
    last_x, last_y = points[-1]
    return (
        f'  <polygon class="spark-fill" points="{area}"/>\n'
        f'  <polyline class="spark-line" points="{line}"/>\n'
        f'  <path class="spark-base" d="M {num(SPARK_L)} {num(SPARK_BASE)} H {num(SPARK_R)}"/>\n'
        f'  <circle class="spark-dot blink still" cx="{num(last_x)}" cy="{num(last_y)}" r="3.5"/>'
    )


def torn_edge():
    """The bottom of the chit, walked right to left to close the paper path."""
    pitch = (CHIT_RIGHT - CHIT_LEFT) / TEETH
    parts = []
    for index in range(TEETH):
        peak = CHIT_RIGHT - (index + 0.5) * pitch
        end = CHIT_RIGHT - (index + 1) * pitch
        parts.append(
            f"L {num(peak)} {num(CHIT_BOTTOM + TOOTH_DROP)} L {num(end)} {CHIT_BOTTOM}"
        )
    return " ".join(parts)


def figure(x, anchor, entry):
    """A supporting stat: the number large, its name small underneath."""
    return (
        f'  <text x="{num(x)}" y="{FIGURE_Y}" text-anchor="{anchor}" class="ink figure">{escape(entry["figure"])}</text>\n'
        f'  <text x="{num(x)}" y="{FIGURE_Y + 18}" text-anchor="{anchor}" class="soft eyebrow">{escape(entry["label"])}</text>'
    )


def render_chit(theme, stats):
    hero, support = hero_and_support(stats)
    quiet = rest_day(stats)
    quiet_desc = (
        f" {WEEKDAYS[quiet]} is so far below the rest that it is marked closed."
        if quiet is not None
        else ""
    )
    support_desc = ", ".join(f"{entry['figure']} {entry['label'].lower()}" for entry in support)

    markup = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">The order chit of Chia Zhi Feng, printed at the Kopi O Kosong Beng stall</title>
  <desc id="desc">A printed order chit. Its headline, shown inside a dial, is {hero["value"]} {hero["caption"]}. Alongside it: {support_desc}. An area chart traces the last {SPARK_DAYS} days, and a strip along the bottom splits the week into seven parts, each as wide as that weekday's share.{quiet_desc}</desc>
  <defs>
    <filter id="grain" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" stitchTiles="stitch"/>
      <feColorMatrix type="saturate" values="0"/>
    </filter>
  </defs>
  <style>{STYLE}  </style>

  <rect class="sheet" width="{WIDTH}" height="{HEIGHT}" rx="{SHEET_R}"/>
  <path class="chit" d="M {CHIT_LEFT} {CHIT_TOP} H {CHIT_RIGHT} V {CHIT_BOTTOM} {torn_edge()} Z"/>

  <text x="{PAD_L}" y="54" class="soft mono meta">KOPI O KOSONG BENG &#183; ORDER #{stats["total_contributions"]:04d} &#183; {stamp(stats["generated_on"])}</text>
  <path class="dot" d="M {PAD_L} 68 H {PAD_R}"/>

  <rect class="pill" x="{PILL_X}" y="{PILL_Y}" width="{num(PILL_W)}" height="{num(PILL_H)}" rx="{num(PILL_H / 2)}"/>
  <text x="{num(PILL_X + PILL_W / 2)}" y="{num(PILL_Y + 14.5)}" text-anchor="middle" class="soft mono eyebrow">{escape(hero["eyebrow"])}</text>

  <circle class="ring-track" cx="{num(RING_CX)}" cy="{num(RING_CY)}" r="{num(RING_R)}"/>
  <path class="ring" d="{ring_arc(hero["gauge"])}"/>
  <text x="{num(RING_CX)}" y="{num(RING_CY + 14)}" text-anchor="middle" class="hero">{escape(hero["value"])}</text>
  <text x="{PAD_L}" y="{num(RING_CY + RING_R + 34)}" class="soft mono caption">{escape(hero["caption"])}</text>

  <text x="{num(SPARK_L)}" y="102" class="soft mono eyebrow">THE LAST {SPARK_DAYS} DAYS</text>
{spark(stats)}
  <path class="dot" d="M {num(SPARK_L)} 218 H {PAD_R}"/>

{figure(SPARK_L, "start", support[0])}
{figure(PAD_R, "end", support[1])}

  <path class="dot" d="M {PAD_L} 300 H {PAD_R}"/>
  <text x="{PAD_L}" y="320" class="soft mono eyebrow">HOW THE WEEK SPLITS</text>
{week_strip(stats)}

  <rect width="{WIDTH}" height="{HEIGHT}" rx="{SHEET_R}" filter="url(#grain)" opacity="0.05"/>
</svg>
"""
    return to_ascii_entities(Template(markup).substitute(palette(theme)))


def load_stats():
    return json.loads(STATS_FILE.read_text(encoding="utf-8"))


def main():
    stats = load_stats()
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for theme in PALETTES:
        target = ASSET_DIR / f"kopi-chit-{theme}.svg"
        with target.open("w", encoding="utf-8", newline="\n") as asset:
            asset.write(render_chit(theme, stats))


if __name__ == "__main__":
    main()
