"""Render the order chit: a printed hawker receipt of the past year.

Pure by contract. Everything drawn here is a function of the stats dict handed
in, which is why the committed asset can still be compared byte for byte
against a fresh render even though the numbers change daily. Nothing in this
module touches the network.

Two things this deliberately is not.

It is not a second glass. The signboard already draws one and already prints
the stack along its specials strip, so a glass here repeated both the picture
and the words.

It is not a contribution grid. A grid of small squares is the graphic GitHub
already puts on the page, and repainting it in a warmer palette would be the
exact borrowed look the guard suite exists to keep off this profile.
"""

from datetime import date, timedelta
from pathlib import Path
from string import Template
from xml.sax.saxutils import escape
import json

from generate_kopi_sign import PALETTES, to_ascii_entities

# The chit borrows the signboard's paper and ink and adds its own five step
# scale for the stains. No value is repeated, here or against the borrowed
# ones, because the light and dark assets are compared by substituting tokens
# back out.
CHIT_TOKENS = {
    "dark": {"g0": "#2A2119"},
    "light": {"g0": "#E6D8C0"},
}

BORROWED = ("paper", "panel", "ink", "ink_soft", "accent", "rule")

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"
STATS_FILE = ROOT / "data" / "stats.json"

WIDTH, HEIGHT = 900, 406

CHIT_LEFT, CHIT_RIGHT = 44, 856
CHIT_TOP, CHIT_BOTTOM = 26, 372
TEETH, TOOTH_DROP = 66, 14
PAD_L, PAD_R = 70, 830

GAUGE_X, GAUGE_W, GAUGE_H = 610, 130.0, 8

# Thirty days, drawn full width and large. A twelve month breakdown was tried
# and thrown out: nine of the twelve months here are empty, so any yearly
# layout is mostly holes no matter how it is drawn. The last month is the
# window where this data is actually dense, and it visibly moves every day.
BARS = 30
BAR_BASELINE = 300.0
BAR_MIN, BAR_MAX = 3.0, 66.0
TICK_Y = 318

MONTHS = (
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
)

STYLE = """
    text { font-family: Georgia, "Iowan Old Style", "Palatino Linotype", "Times New Roman", serif; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
    .ink { fill: $ink; }
    .soft { fill: $ink_soft; }
    .chit { fill: $panel; stroke: $rule; stroke-width: 1.5; }
    .dot { fill: none; stroke: $rule; stroke-width: 1; stroke-dasharray: 1 3; }
    .rule { fill: none; stroke: $rule; stroke-width: 1; }
    .head { font-size: 17px; font-weight: 700; letter-spacing: 2.8px; }
    .meta { font-size: 9px; letter-spacing: 1.6px; }
    .item { font-size: 11.5px; letter-spacing: 0.4px; }
    .label { font-size: 9px; letter-spacing: 3px; }
    .tick { font-size: 7.5px; letter-spacing: 1.4px; }
    .track { fill: $g0; }
    .gauge { fill: $accent; }
    .bar { fill: $accent; }
    .bar-idle { fill: $g0; }
    /* Only today's bar moves, and it rests at full opacity, so a
       renderer parked at t=0 shows the finished card. An earlier version
       animated the artwork itself and rendered wrong wherever the animation
       was not running. */
    .today { animation: settle 3.4s ease-in-out infinite; }
    @keyframes settle {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
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


def fill_fraction(stats):
    total = stats.get("days_total") or 0
    if total <= 0:
        return 0.0
    return max(0.0, min(1.0, stats.get("days_active", 0) / total))


def recent(stats):
    """The last thirty days, oldest first, padded if the history is shorter."""
    tail = (stats.get("daily") or [])[-BARS:]
    return [0] * (BARS - len(tail)) + tail


def bar_heights(counts):
    """Height is a length, so it scales linearly. That is the honest encoding
    for a bar, unlike a circle, whose area does the reading."""
    peak = max(counts) if counts else 0
    if peak <= 0:
        return [BAR_MIN] * len(counts)
    return [
        BAR_MIN if value <= 0 else BAR_MIN + (BAR_MAX - BAR_MIN) * (value / peak)
        for value in counts
    ]


def bars(stats):
    counts = recent(stats)
    heights = bar_heights(counts)
    pitch = (PAD_R - PAD_L) / BARS
    width = pitch - 8
    newest = len(counts) - 1
    rows = []
    for index, height in enumerate(heights):
        style = "bar" if counts[index] > 0 else "bar-idle"
        if index == newest and counts[index] > 0:
            style += " today still"
        rows.append(
            f'  <rect class="{style}" x="{num(PAD_L + index * pitch)}" '
            f'y="{num(BAR_BASELINE - height)}" width="{num(width)}" '
            f'height="{num(height)}" rx="2.5"/>'
        )
    return "\n".join(rows)


def window_label(stats):
    """The date the leftmost bar stands for, so the axis is not a mystery."""
    end = stats.get("window_end")
    if not end:
        return ""
    return stamp((date.fromisoformat(end) - timedelta(days=BARS - 1)).isoformat())


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


def line_item(y, label, value):
    return (
        f'  <text x="{PAD_L}" y="{y}" class="ink mono item">{escape(label)}</text>\n'
        f'  <text x="{PAD_R}" y="{y}" text-anchor="end" class="ink mono item">{escape(value)}</text>'
    )


def gauge(y, fraction):
    return (
        f'  <rect class="track" x="{GAUGE_X}" y="{y - 8}" width="{num(GAUGE_W)}" height="{GAUGE_H}" rx="4"/>\n'
        f'  <rect class="gauge" x="{GAUGE_X}" y="{y - 8}" width="{num(GAUGE_W * fraction)}" height="{GAUGE_H}" rx="4"/>'
    )


def render_chit(theme, stats):
    fraction = fill_fraction(stats)
    served = stamp(stats["window_start"]) if stats.get("window_start") else ""

    markup = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">The order chit of Chia Zhi Feng, printed at the Kopi O Kosong Beng stall</title>
  <desc id="desc">A printed order chit listing {count(stats["total_contributions"])} contributions in the past year, a longest unbroken streak of {days_label(stats["longest_run"])}, and {stats["days_active"]} active days out of {stats["days_total"]}. Below the totals a bar chart shows the last thirty days, one bar per day, taller on the busier days.</desc>
  <style>{STYLE}  </style>

  <rect width="{WIDTH}" height="{HEIGHT}" rx="14" fill="$paper"/>
  <path class="chit" d="M {CHIT_LEFT} {CHIT_TOP} H {CHIT_RIGHT} V {CHIT_BOTTOM} {torn_edge()} Z"/>

  <text x="{PAD_L}" y="64" class="ink head">KOPI O KOSONG BENG</text>
  <text x="{PAD_L}" y="84" class="soft mono meta">ORDER #{stats["total_contributions"]:04d} &#183; {stamp(stats["generated_on"])}</text>
  <path class="dot" d="M {PAD_L} 100 H {PAD_R}"/>

{line_item(128, "commits, past year", count(stats["total_contributions"]))}
{line_item(152, "longest streak", days_label(stats["longest_run"]))}
{line_item(176, "days active", f'{stats["days_active"]} of {stats["days_total"]}')}
{gauge(176, fraction)}

  <path class="dot" d="M {PAD_L} 196 H {PAD_R}"/>
  <text x="{PAD_L}" y="216" class="soft label">THE LAST THIRTY DAYS</text>
{bars(stats)}
  <path class="rule" d="M {PAD_L} {num(BAR_BASELINE + 3)} H {PAD_R}"/>
  <text x="{PAD_L}" y="{TICK_Y}" class="soft mono tick">{escape(window_label(stats))}</text>
  <text x="{PAD_R}" y="{TICK_Y}" text-anchor="end" class="soft mono tick">TODAY</text>

  <path class="dot" d="M {PAD_L} 334 H {PAD_R}"/>
  <text x="{PAD_L}" y="356" class="soft label">COUNTING SINCE</text>
  <text x="{PAD_R}" y="356" text-anchor="end" class="ink mono item">{escape(served)}</text>
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
