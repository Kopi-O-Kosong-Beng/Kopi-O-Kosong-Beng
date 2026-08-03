"""Render the order chit: what a year of this account actually says.

Pure by contract. Everything drawn here is a function of the stats dict handed
in, which is why the committed asset can still be compared byte for byte
against a fresh render even though the numbers change daily. Nothing in this
module touches the network.

The card is meant to say something the profile page does not already say.
A total and a streak are just the same numbers GitHub prints, so the three
findings on it are derived: how much of the year landed in its ten busiest
days, which weekday the stall is effectively shut, and when the best run ran.

Several earlier shapes were tried and thrown out, each recorded in the design
doc: a second glass repeated the signboard, a calendar of small squares was
GitHub's own graphic in a warmer palette, and twelve monthly cup rings were
mostly empty because nine of the twelve months here have nothing in them.
"""

from datetime import date, timedelta
from pathlib import Path
from string import Template
from xml.sax.saxutils import escape
import json

from generate_kopi_sign import PALETTES, to_ascii_entities

CHIT_TOKENS = {
    "dark": {"g0": "#2A2119"},
    "light": {"g0": "#E6D8C0"},
}

BORROWED = ("paper", "panel", "ink", "ink_soft", "accent", "rule", "glass")

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"
STATS_FILE = ROOT / "data" / "stats.json"

WIDTH, HEIGHT = 900, 426

CHIT_LEFT, CHIT_RIGHT = 44, 856
CHIT_TOP, CHIT_BOTTOM = 26, 392
TEETH, TOOTH_DROP = 66, 14
PAD_L, PAD_R = 70, 830

# The gauge sits in the empty middle column. Further right it collided with
# the value, which is right aligned and long enough to reach back past 720.
GAUGE_X, GAUGE_W, GAUGE_H = 300, 220.0, 8

# Seven glasses, one per weekday, each poured to how much that day carries.
# Small and plain on purpose: no straw, no ice, no condensation. These are
# data marks, and the one detailed glass on the profile stays on the signboard.
GLASS_TOP, GLASS_BOTTOM = 226.0, 312.0
GLASS_TOP_HW, GLASS_BOT_HW = 27.0, 21.0
GLASS_FULL, GLASS_EMPTY = 234.0, 304.0
DOW_LABEL_Y = 330
DOW_TAG_Y = 344

BURST_DAYS = 10

MONTHS = (
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
)
WEEKDAYS = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")

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
    .day { font-size: 9px; letter-spacing: 2px; }
    .tag { font-size: 8px; letter-spacing: 1.6px; fill: $accent; }
    .track { fill: $g0; }
    .gauge { fill: $accent; }
    .tumbler { fill: $panel; stroke: $glass; stroke-width: 2; stroke-linejoin: round; }
    .pour { fill: $accent; }
    .pour-quiet { fill: $g0; }
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
    """Monday first, matching the labels printed under the bars."""
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
    average = sum(totals) / 7
    return quietest if totals[quietest] * 3 < average else None


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


def pour_levels(values):
    """Share of the busiest weekday, which becomes how full each glass is.

    Level is a length up the side of the glass, so it scales linearly. That is
    the honest encoding here, unlike a circle, which is read by its area.
    """
    peak = max(values) if values else 0
    if peak <= 0:
        return [0.0] * len(values)
    return [max(0.0, value / peak) for value in values]


def surface_y(level):
    return GLASS_EMPTY - level * (GLASS_EMPTY - GLASS_FULL)


def tumbler_path(centre):
    """A plain tapered tumbler. No straw, no ice: this is a data mark."""
    return (
        f"M {num(centre - GLASS_TOP_HW)} {num(GLASS_TOP)} "
        f"L {num(centre - GLASS_BOT_HW)} {num(GLASS_BOTTOM - 8)} "
        f"Q {num(centre - GLASS_BOT_HW)} {num(GLASS_BOTTOM)} {num(centre - GLASS_BOT_HW + 8)} {num(GLASS_BOTTOM)} "
        f"L {num(centre + GLASS_BOT_HW - 8)} {num(GLASS_BOTTOM)} "
        f"Q {num(centre + GLASS_BOT_HW)} {num(GLASS_BOTTOM)} {num(centre + GLASS_BOT_HW)} {num(GLASS_BOTTOM - 8)} "
        f"L {num(centre + GLASS_TOP_HW)} {num(GLASS_TOP)} Z"
    )


def weekday_glasses(stats):
    levels = pour_levels(weekday_totals(stats))
    quiet = rest_day(stats)
    pitch = (PAD_R - PAD_L) / 7
    rows = []
    for index, level in enumerate(levels):
        centre = PAD_L + (index + 0.5) * pitch
        path = tumbler_path(centre)
        surface = surface_y(level)
        style = "pour-quiet" if index == quiet else "pour"
        rows.append(f'  <clipPath id="cup-{index}"><path d="{path}"/></clipPath>')
        rows.append(f'  <path class="tumbler" d="{path}"/>')
        if level > 0:
            rows.append(
                f'  <rect class="{style}" clip-path="url(#cup-{index})" '
                f'x="{num(centre - GLASS_TOP_HW - 2)}" y="{num(surface)}" '
                f'width="{num(2 * GLASS_TOP_HW + 4)}" height="{num(GLASS_BOTTOM + 4 - surface)}"/>'
            )
        rows.append(
            f'  <text x="{num(centre)}" y="{DOW_LABEL_Y}" text-anchor="middle" '
            f'class="soft day">{WEEKDAYS[index]}</text>'
        )
        if index == quiet:
            rows.append(
                f'  <text x="{num(centre)}" y="{DOW_TAG_Y}" text-anchor="middle" '
                f'class="tag mono blink still">rest day</text>'
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


def streak_value(stats):
    end = best_run_end(stats)
    run = days_label(stats["longest_run"])
    return f"{run} to {short_stamp(end)}" if end else run


def render_chit(theme, stats):
    share = burst_share(stats)
    quiet = rest_day(stats)
    quiet_desc = (
        f" The quietest weekday by a wide margin is {WEEKDAYS[quiet]}."
        if quiet is not None
        else ""
    )

    markup = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">The order chit of Chia Zhi Feng, printed at the Kopi O Kosong Beng stall</title>
  <desc id="desc">A printed order chit. Over the past year: {count(stats["total_contributions"])} contributions, a longest unbroken streak of {days_label(stats["longest_run"])}, and {share:.0%} of the whole year landing in its {BURST_DAYS} busiest days, which says the work comes in bursts rather than a steady drip. Below that, seven glasses compare how much lands on each weekday, each poured as full as that day is busy.{quiet_desc}</desc>
  <style>{STYLE}  </style>

  <rect width="{WIDTH}" height="{HEIGHT}" rx="14" fill="$paper"/>
  <path class="chit" d="M {CHIT_LEFT} {CHIT_TOP} H {CHIT_RIGHT} V {CHIT_BOTTOM} {torn_edge()} Z"/>

  <text x="{PAD_L}" y="64" class="ink head">KOPI O KOSONG BENG</text>
  <text x="{PAD_L}" y="84" class="soft mono meta">ORDER #{stats["total_contributions"]:04d} &#183; {stamp(stats["generated_on"])}</text>
  <path class="dot" d="M {PAD_L} 100 H {PAD_R}"/>

{line_item(128, "commits, past year", count(stats["total_contributions"]))}
{line_item(152, "longest streak", streak_value(stats))}
{line_item(176, f"busiest {BURST_DAYS} days", f"{share:.0%} of the year")}
{gauge(176, share)}

  <path class="dot" d="M {PAD_L} 196 H {PAD_R}"/>
  <text x="{PAD_L}" y="216" class="soft label">HOW THE WEEK POURS</text>
{weekday_glasses(stats)}

  <path class="dot" d="M {PAD_L} 358 H {PAD_R}"/>
  <text x="{PAD_L}" y="380" class="soft label">COUNTING SINCE</text>
  <text x="{PAD_R}" y="380" text-anchor="end" class="ink mono item">{escape(stamp(stats["window_start"]))}</text>
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
