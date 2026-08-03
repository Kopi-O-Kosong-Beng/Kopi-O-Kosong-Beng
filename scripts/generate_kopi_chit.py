"""Render the order chit: a printed hawker receipt plus a filling glass.

Pure by contract. Everything drawn here is a function of the stats dict handed
in, which is why the committed asset can still be compared byte for byte
against a fresh render even though the numbers change daily. Nothing in this
module touches the network.
"""

from datetime import date
from pathlib import Path
from string import Template
from xml.sax.saxutils import escape
import json

from generate_kopi_sign import PALETTES, STACK, to_ascii_entities

# The signboard's flat brown reads fine as a full glass. A shallow pour is a
# small shape sitting on the panel, and in dark that brown all but vanishes
# against it, so the liquid gets its own two tokens instead of borrowing one
# tuned for a different job. No value is repeated, here or in PALETTES, because
# the light and dark assets are compared by substituting tokens back out.
CHIT_TOKENS = {
    "dark": {"brew": "#6B3F1C", "crema": "#9C6A2E"},
    "light": {"brew": "#472A15", "crema": "#7A4A22"},
}

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"
STATS_FILE = ROOT / "data" / "stats.json"

WIDTH, HEIGHT = 900, 360

CHIT_LEFT, CHIT_RIGHT = 44, 592
CHIT_TOP, CHIT_BOTTOM = 26, 302
TEETH, TOOTH_DROP = 44, 14
PAD_L, PAD_R = 70, 566

BAR_COUNT = 30
BAR_BASELINE = 248.0
BAR_MIN, BAR_MAX = 2.0, 34.0
BAR_WIDTH = 9.0

GLASS_CX = 752
GLASS_TOP, GLASS_BOTTOM = 58, 320
GLASS_TOP_RX, GLASS_BOTTOM_RX = 64.0, 38.0

# The glass is empty at 0.0 and brim full at 1.0, so a silent year reads as an
# empty glass rather than a flattering sliver.
GLASS_TOP_LEVEL, GLASS_BOTTOM_LEVEL = 72.0, 320.0

MONTHS = (
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
)

# x, y, size, rotation. Ice is heaped through the whole glass rather than
# floated on the surface, so a shallow pour still looks like a real iced kopi
# instead of cubes hanging in mid air.
CUBES = (
    (704, 84, 42, -11),
    (752, 100, 38, 8),
    (710, 142, 36, 5),
    (754, 162, 34, -7),
    (706, 198, 32, 10),
    (752, 226, 30, -4),
)

STYLE = """
    text { font-family: Georgia, "Iowan Old Style", "Palatino Linotype", "Times New Roman", serif; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
    .ink { fill: $ink; }
    .soft { fill: $ink_soft; }
    .chit { fill: $panel; stroke: $rule; stroke-width: 1.5; }
    .dot { fill: none; stroke: $rule; stroke-width: 1; stroke-dasharray: 1 3; }
    .rule { fill: none; stroke: $rule; stroke-width: 1; }
    .head { font-size: 15px; font-weight: 700; letter-spacing: 2.6px; }
    .meta { font-size: 9px; letter-spacing: 1.6px; }
    .item { font-size: 11.5px; letter-spacing: 0.4px; }
    .label { font-size: 9px; letter-spacing: 3px; }
    .spark { fill: $accent; }
    .spark-idle { fill: $rule; }
    .brew { fill: $brew; }
    .brew-top { fill: $crema; }
    .ice { fill: $ice; fill-opacity: 0.92; stroke: $ice_line; stroke-width: 1; }
    .cube { fill: $coffee; text-anchor: middle; letter-spacing: 0.2px; }
    .glass { fill: none; stroke: $glass; stroke-width: 2.4; stroke-linejoin: round; }
    .straw { fill: none; stroke: $accent; stroke-width: 4; stroke-linecap: round; }
    .drop { fill: $ice; opacity: 0; }
    .drop-a { animation: bead 5s ease-in 0s infinite; }
    .drop-b { animation: bead 5s ease-in 1.7s infinite; }
    .drop-c { animation: bead 5s ease-in 3.4s infinite; }
    /* No fill-mode and no delay on purpose. The resting state of the coffee
       has to be its final level, because anything that does not run the
       animation, a still thumbnail or a reduced motion viewer, must still see
       a full glass rather than an empty one. */
    .pour { animation: pour 1.8s cubic-bezier(0.2, 0.75, 0.25, 1) 1; }
    @keyframes bead {
      0% { transform: translateY(0px); opacity: 0; }
      12% { opacity: 0.85; }
      70% { opacity: 0.7; }
      100% { transform: translateY(44px); opacity: 0; }
    }
    @keyframes pour {
      from { transform: translateY(160px); }
      to { transform: translateY(0px); }
    }
    @media (prefers-reduced-motion: reduce) {
      .motion { animation: none !important; opacity: 0.7 !important; }
      .pour { animation: none !important; }
    }
"""


def palette(theme):
    """The signboard palette plus the chit only liquid tokens."""
    return {**PALETTES[theme], **CHIT_TOKENS[theme]}


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


def surface_y(fill):
    return GLASS_BOTTOM_LEVEL - fill * (GLASS_BOTTOM_LEVEL - GLASS_TOP_LEVEL)


def glass_half_width(y):
    ratio = (y - GLASS_TOP) / (GLASS_BOTTOM - GLASS_TOP)
    return GLASS_TOP_RX - ratio * (GLASS_TOP_RX - GLASS_BOTTOM_RX)


def bar_heights(counts):
    peak = max(counts) if counts else 0
    if peak <= 0:
        return [BAR_MIN] * len(counts)
    return [
        BAR_MIN if value <= 0 else BAR_MIN + (BAR_MAX - BAR_MIN) * (value / peak)
        for value in counts
    ]


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
        f'  <text x="{PAD_L}" y="{y}" class="ink mono item">1x&#160;&#160;&#160;{escape(label)}</text>\n'
        f'  <text x="{PAD_R}" y="{y}" text-anchor="end" class="ink mono item">{escape(value)}</text>'
    )


def sparkline(counts):
    heights = bar_heights(counts)
    pitch = (PAD_R - PAD_L) / BAR_COUNT
    rows = []
    for index, height in enumerate(heights):
        style = "spark" if counts[index] > 0 else "spark-idle"
        rows.append(
            f'  <rect class="{style}" x="{num(PAD_L + index * pitch)}" '
            f'y="{num(BAR_BASELINE - height)}" width="{num(BAR_WIDTH)}" '
            f'height="{num(height)}" rx="1.5"/>'
        )
    return "\n".join(rows)


def ice_cubes(stack):
    rows = []
    for (x, y, size, rotation), (_, short) in zip(CUBES, stack):
        cx, cy = x + size / 2, y + size / 2
        font = 11 if size >= 40 else 10 if size >= 36 else 9 if size >= 32 else 8
        rows.append(
            f'    <g transform="rotate({num(rotation)} {num(cx)} {num(cy)})">\n'
            f'      <rect class="ice" x="{x}" y="{y}" width="{size}" height="{size}" rx="4"/>\n'
            f'      <text class="cube mono" x="{num(cx)}" y="{num(cy + font / 3)}" '
            f'font-size="{font}">{escape(short)}</text>\n'
            f"    </g>"
        )
    return "\n".join(rows)


def render_chit(theme, stats, stack=STACK):
    fill = fill_fraction(stats)
    surface = surface_y(fill)
    labels = [short for _, short in stack]
    glass_body = (
        f"M {GLASS_CX - GLASS_TOP_RX:.0f} {GLASS_TOP} L 700 308 Q 702 320 714 320 "
        f"L 790 320 Q 802 320 804 308 L {GLASS_CX + GLASS_TOP_RX:.0f} {GLASS_TOP}"
    )

    markup = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">The order chit of Chia Zhi Feng, printed at the Kopi O Kosong Beng stall</title>
  <desc id="desc">A printed order chit listing {count(stats["total_contributions"])} contributions in the past year, a longest run of {days_label(stats["longest_run"])}, and {stats["days_active"]} of {stats["days_total"]} days brewed, above a bar chart of the last thirty days. Beside it stands a tall glass of iced kopi filled to the share of days brewed, its ice cubes stamped {escape(", ".join(labels))}.</desc>
  <style>{STYLE}  </style>

  <rect width="{WIDTH}" height="{HEIGHT}" rx="14" fill="$paper"/>
  <path class="chit" d="M {CHIT_LEFT} {CHIT_TOP} H {CHIT_RIGHT} V {CHIT_BOTTOM} {torn_edge()} Z"/>

  <text x="{PAD_L}" y="62" class="ink head">KOPI O KOSONG BENG</text>
  <text x="{PAD_L}" y="80" class="soft mono meta">ORDER #{stats["total_contributions"]:04d} &#183; {stamp(stats["generated_on"])}</text>
  <path class="dot" d="M {PAD_L} 96 H {PAD_R}"/>

{line_item(122, "commits, past year", count(stats["total_contributions"]))}
{line_item(146, "longest run", days_label(stats["longest_run"]))}
{line_item(170, "days brewed", f'{stats["days_active"]}/{stats["days_total"]}')}

  <path class="dot" d="M {PAD_L} 188 H {PAD_R}"/>
  <text x="{PAD_L}" y="206" class="soft label">LAST 30 DAYS</text>
{sparkline(stats["recent"])}
  <path class="rule" d="M {PAD_L} {num(BAR_BASELINE + 2)} H {PAD_R}"/>

  <path class="dot" d="M {PAD_L} 266 H {PAD_R}"/>
  <text x="{PAD_L}" y="288" class="soft label">TOTAL</text>
  <text x="{PAD_R}" y="288" text-anchor="end" class="ink mono item">no sugar</text>

  <path class="rule" d="M 620 44 V 330"/>

  <g aria-label="A tall glass of iced kopi, filled to the share of days brewed">
    <clipPath id="glass-body"><path d="{glass_body} Z"/></clipPath>
    <g clip-path="url(#glass-body)">
      <g class="pour">
        <rect class="brew" x="680" y="{num(surface)}" width="144" height="{num(GLASS_BOTTOM + 6 - surface)}"/>
        <ellipse class="brew-top" cx="{GLASS_CX}" cy="{num(surface)}" rx="{num(glass_half_width(surface))}" ry="5"/>
      </g>
    </g>
    <path class="straw" d="M 796 30 L 740 302"/>
{ice_cubes(stack)}
    <path class="glass" d="{glass_body}"/>
    <ellipse class="glass" cx="{GLASS_CX}" cy="{GLASS_TOP}" rx="{num(GLASS_TOP_RX)}" ry="13"/>
    <ellipse class="drop motion drop-a" cx="692" cy="130" rx="2.8" ry="3.8"/>
    <ellipse class="drop motion drop-b" cx="812" cy="170" rx="2.4" ry="3.4"/>
    <ellipse class="drop motion drop-c" cx="696" cy="220" rx="2.2" ry="3"/>
  </g>

  <text x="{GLASS_CX}" y="344" text-anchor="middle" class="soft label">TODAY'S BREW</text>
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
