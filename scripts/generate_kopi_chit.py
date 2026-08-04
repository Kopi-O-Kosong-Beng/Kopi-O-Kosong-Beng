"""Render the numbers: one overall stats card for the account.

Pure by contract. Everything drawn here is a function of the stats dict handed
in, which is why the committed asset can still be compared byte for byte
against a fresh render even though the numbers change daily. Nothing in this
module touches the network.

One caveat is baked into the layout rather than argued about. The year total is
honest but the year *ratio* is not flattering on this account: it was genuinely
quiet until recently, so 45 of 366 days would read as dormant while 27 of the
last 30 reads as someone shipping. The card therefore reports the year as a
count and reports rate over the recent window, which is the same data framed
where it is true of how the account behaves now.
"""

from datetime import date
from pathlib import Path
from string import Template
from xml.sax.saxutils import escape
import json

from generate_kopi_sign import PALETTES, to_ascii_entities

BORROWED = ("paper", "panel", "ink", "ink_soft", "accent", "rule")

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"
STATS_FILE = ROOT / "data" / "stats.json"

WIDTH, HEIGHT = 900, 356

# Nested enclosures: the outer sheet holds the chit, which sits inset with its
# own hairline. A card laid flat on one background reads as a screenshot.
SHEET_R = 26
CHIT_LEFT, CHIT_RIGHT = 24, 876
CHIT_TOP, CHIT_BOTTOM = 22, 316
TEETH, TOOTH_DROP = 68, 14

PAD_L, PAD_R = 62, 838

# Georgia sets old style figures, so 3, 4, 7 and 9 drop below the
# baseline. The label needs clearance the cap height alone does not imply.
HERO_Y, HERO_LABEL_Y = 142, 180

SPARK_L, SPARK_R = 380.0, 838.0
SPARK_BASE, SPARK_H = 178.0, 72.0
SPARK_DAYS = 30

# Four columns across the full width, left aligned so the eye can run down them.
COLUMNS = (62, 256, 450, 644)
FIGURE_Y, FIGURE_LABEL_Y = 240, 258

FOOTER_Y = 300

MONTHS = (
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
)

STYLE = """
    text { font-family: Georgia, "Iowan Old Style", "Palatino Linotype", "Times New Roman", serif; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
    .ink { fill: $ink; }
    .soft { fill: $ink_soft; }
    .sheet { fill: $paper; }
    .chit { fill: $panel; stroke: $rule; stroke-width: 1.25; }
    .dot { fill: none; stroke: $rule; stroke-width: 1; stroke-dasharray: 1 3; }
    .meta { font-size: 9px; letter-spacing: 1.8px; }
    .eyebrow { font-size: 8px; letter-spacing: 2.4px; }
    .hero { font-size: 76px; font-weight: 700; letter-spacing: -2.5px; fill: $accent; }
    .figure { font-size: 27px; font-weight: 700; letter-spacing: -0.4px; }
    .spark-fill { fill: $accent; opacity: 0.16; }
    .spark-line { fill: none; stroke: $accent; stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
    .spark-base { fill: none; stroke: $rule; stroke-width: 1; }
    .spark-dot { fill: $accent; }
    /* Only today's dot on the chart moves, and it rests at full opacity, so a
       renderer parked at t=0 shows the finished card. An earlier version
       animated the artwork itself and rendered wrong wherever the animation
       was not running. */
    .blink { animation: settle 2.6s ease-in-out infinite; }
    @keyframes settle {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.35; }
    }
    @media (prefers-reduced-motion: reduce) {
      .still { animation: none !important; }
    }
"""


def palette(theme):
    """Only what the chit actually paints with, so a dead token is a failure.

    The card carries no colour of its own any more. Earlier versions needed a
    faint tone for chips and a ring track; both are gone, and an unused token
    would sit here looking like an intention.
    """
    return {key: PALETTES[theme][key] for key in BORROWED}


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


def recent(stats):
    """The last thirty days, oldest first, padded if the history is shorter."""
    tail = (stats.get("daily") or [])[-SPARK_DAYS:]
    return [0] * (SPARK_DAYS - len(tail)) + tail


def busiest_day(stats):
    daily = stats.get("daily") or []
    return max(daily) if daily else 0


def recent_active(stats):
    return sum(1 for value in recent(stats) if value > 0)


def days_since_served(stats):
    """How long since anything was pushed. None when nothing ever was.

    Counted back from the end of the window rather than from today, so the
    answer stays true to the data the card was actually built from.
    """
    for offset, value in enumerate(reversed(stats.get("daily") or [])):
        if value > 0:
            return offset
    return None


def served_label(stats):
    gap = days_since_served(stats)
    if gap is None:
        return "NOT YET"
    if gap == 0:
        return "TODAY"
    if gap == 1:
        return "YESTERDAY"
    return f"{gap} DAYS AGO"


def figures(stats):
    """The four supporting numbers, in the order they are read.

    Rate is reported over the recent window and volume over the year. Reporting
    rate over the year would print 45 of 366 on an account that was simply not
    busy yet, which reads as dormant rather than as new.
    """
    return (
        (days_label(stats.get("longest_run", 0)), "LONGEST STREAK"),
        (days_label(stats.get("current_run", 0)), "CURRENT STREAK"),
        (count(busiest_day(stats)), "BUSIEST DAY"),
        (f"{recent_active(stats)}/{SPARK_DAYS}", f"ACTIVE, LAST {SPARK_DAYS} DAYS"),
    )


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


def figure_row(stats):
    rows = []
    for x, (value, label) in zip(COLUMNS, figures(stats)):
        rows.append(
            f'  <text x="{x}" y="{FIGURE_Y}" class="ink figure">{escape(value)}</text>\n'
            f'  <text x="{x}" y="{FIGURE_LABEL_Y}" class="soft eyebrow">{escape(label)}</text>'
        )
    return "\n".join(rows)


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


def render_chit(theme, stats):
    total = stats.get("total_contributions", 0)
    spoken = ", ".join(f"{value} {label.lower()}" for value, label in figures(stats))

    markup = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">The numbers at Kopi O Kosong Beng, the GitHub account of Chia Zhi Feng</title>
  <desc id="desc">A printed stats chit. {count(total)} contributions over the past year, with {spoken}. An area chart traces the last {SPARK_DAYS} days, and a line at the foot says the account last pushed {served_label(stats).lower()}.</desc>
  <defs>
    <filter id="grain" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" stitchTiles="stitch"/>
      <feColorMatrix type="saturate" values="0"/>
    </filter>
  </defs>
  <style>{STYLE}  </style>

  <rect class="sheet" width="{WIDTH}" height="{HEIGHT}" rx="{SHEET_R}"/>
  <path class="chit" d="M {CHIT_LEFT} {CHIT_TOP} H {CHIT_RIGHT} V {CHIT_BOTTOM} {torn_edge()} Z"/>

  <text x="{PAD_L}" y="54" class="soft mono meta">THE NUMBERS &#183; KOPI O KOSONG BENG &#183; {stamp(stats["generated_on"])}</text>
  <path class="dot" d="M {PAD_L} 68 H {PAD_R}"/>

  <text x="{PAD_L}" y="{HERO_Y}" class="hero">{count(total)}</text>
  <text x="{PAD_L}" y="{HERO_LABEL_Y}" class="soft eyebrow">CONTRIBUTIONS, PAST YEAR</text>

  <text x="{num(SPARK_L)}" y="100" class="soft mono eyebrow">THE LAST {SPARK_DAYS} DAYS</text>
{spark(stats)}

  <path class="dot" d="M {PAD_L} 200 H {PAD_R}"/>
{figure_row(stats)}
  <path class="dot" d="M {PAD_L} 278 H {PAD_R}"/>

  <text x="{PAD_L}" y="{FOOTER_Y}" class="soft mono eyebrow">LAST PUSHED</text>
  <text x="{PAD_R}" y="{FOOTER_Y}" text-anchor="end" class="ink mono eyebrow">{served_label(stats)}</text>

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
