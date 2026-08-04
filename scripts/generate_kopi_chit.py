"""Render the counter: what is being built, and what it is built with.

Pure by contract. Everything drawn here is a function of the curated COUNTER
list plus the stats dict handed in, which is why the committed asset can still
be compared byte for byte against a fresh render. Nothing here touches the
network.

This card used to report activity: commits, streaks, the share of the year that
landed in its ten busiest days, which weekday was quietest. Every one was true
and none was worth a stranger's forty seconds. Several actively worked against
him. Over 366 days the account read as dormant, because it genuinely was until
recently, and a quietest weekday reads as "does not work Fridays".

So the card points at the work instead. A visitor wants to know what this person
builds and what they build it with, and the README says the first in prose and
never says the second at all. Nothing here decays when a habit changes, and
there is no number that can undersell anyone.

The one live element is the footer. Proof that an account is not abandoned is
the single thing activity data can usefully tell a visitor, and it costs a line.
"""

from datetime import date
from pathlib import Path
from string import Template
from xml.sax.saxutils import escape
import json

from generate_kopi_sign import PALETTES, to_ascii_entities

# Curated by hand, exactly like the signboard stack. Edit this to change the
# card and the daily workflow will redraw it. The stack tags are inferred from
# how each project is described in the README, so correct any that are wrong.
COUNTER = (
    {
        "name": "pitchMe",
        "note": "LIVE",
        "line": "an AI speaking coach. you talk, it tells you the truth.",
        "stack": ("typescript", "gcp"),
    },
    {
        "name": "a robot arm",
        "note": "SUTD",
        "line": "taught to pick things up without dropping them.",
        "stack": ("python", "ros"),
    },
    {
        "name": "a two player math game",
        "note": "SUTD",
        "line": "no CPU in it. just wires and states.",
        "stack": ("fpga",),
    },
    {
        "name": "quantum devices",
        "note": "CLEANROOM",
        "line": "made at hours I would rather not say.",
        "stack": ("python",),
    },
)

CHIT_TOKENS = {
    "dark": {"g0": "#2A2119"},
    "light": {"g0": "#E6D8C0"},
}

BORROWED = ("paper", "panel", "ink", "ink_soft", "accent", "rule")

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"
STATS_FILE = ROOT / "data" / "stats.json"

WIDTH, HEIGHT = 900, 450

# Nested enclosures: the outer sheet holds the chit, which sits inset with its
# own hairline. A card laid flat on one background reads as a screenshot.
SHEET_R = 26
CHIT_LEFT, CHIT_RIGHT = 24, 876
CHIT_TOP, CHIT_BOTTOM = 22, 410
TEETH, TOOTH_DROP = 68, 14

PAD_L, PAD_R = 62, 838

ROW_TOP, ROW_H = 86, 70
CHIP_H, CHIP_GAP, CHIP_PAD = 16.0, 6.0, 9.0
CHIP_CHAR = 5.4

FOOTER_Y = 394

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
    .name { font-size: 19px; font-weight: 700; letter-spacing: 0.2px; }
    .note { font-size: 8.5px; letter-spacing: 2px; fill: $accent; }
    .line { font-size: 11.5px; letter-spacing: 0.2px; }
    .chip { fill: $g0; }
    .chip-text { font-size: 8px; letter-spacing: 1.4px; }
    .pulse { fill: $accent; }
    /* Only the live dot moves, and it rests at full opacity, so a renderer
       parked at t=0 shows the finished card. An earlier version animated the
       artwork itself and rendered wrong wherever the animation was not
       running. */
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
    """Only what the chit actually paints with, so a dead token is a failure."""
    borrowed = {key: PALETTES[theme][key] for key in BORROWED}
    return {**borrowed, **CHIT_TOKENS[theme]}


def num(value):
    """Trim float noise so the asset is byte stable across platforms."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


def stamp(iso):
    """Format without strftime, which would drag in the runner's locale."""
    day = date.fromisoformat(iso)
    return f"{day.day:02d} {MONTHS[day.month - 1]} {day.year}"


def days_since_served(stats):
    """How long since anything was pushed. None when nothing ever was.

    Counted back from the end of the window rather than from today, so the
    answer stays true to the data the card was actually built from.
    """
    daily = stats.get("daily") or []
    for offset, value in enumerate(reversed(daily)):
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


def chips(x, y, stack):
    """Small filled pills. Width is estimated from the monospace advance, which
    is safe here because the tag font stack is monospace all the way down."""
    out = []
    for tag in stack:
        width = len(tag) * CHIP_CHAR + 2 * CHIP_PAD
        out.append(
            f'    <rect class="chip" x="{num(x)}" y="{num(y)}" width="{num(width)}" '
            f'height="{num(CHIP_H)}" rx="{num(CHIP_H / 2)}"/>\n'
            f'    <text x="{num(x + width / 2)}" y="{num(y + 11)}" text-anchor="middle" '
            f'class="soft mono chip-text">{escape(tag)}</text>'
        )
        x += width + CHIP_GAP
    return "\n".join(out)


def rows():
    out = []
    for index, entry in enumerate(COUNTER):
        top = ROW_TOP + index * ROW_H
        dot = (
            f'    <circle class="pulse blink still" cx="{PAD_R - 38}" cy="{top + 14}" r="3"/>\n'
            if entry["note"] == "LIVE"
            else ""
        )
        out.append(
            "  <g>\n"
            f'    <text x="{PAD_L}" y="{top + 18}" class="ink name">{escape(entry["name"])}</text>\n'
            f"{dot}"
            f'    <text x="{PAD_R}" y="{top + 17}" text-anchor="end" class="mono note">{escape(entry["note"])}</text>\n'
            f'    <text x="{PAD_L}" y="{top + 37}" class="soft mono line">{escape(entry["line"])}</text>\n'
            f'{chips(PAD_L, top + 44, entry["stack"])}\n'
            "  </g>"
        )
        if index < len(COUNTER) - 1:
            out.append(f'  <path class="dot" d="M {PAD_L} {top + 64} H {PAD_R}"/>')
    return "\n".join(out)


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
    listing = "; ".join(
        f"{entry['name']}, {entry['line']} built with {', '.join(entry['stack'])}"
        for entry in COUNTER
    )

    markup = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">The counter at Kopi O Kosong Beng: what Chia Zhi Feng is building</title>
  <desc id="desc">A printed chit listing what is on the counter. {escape(listing)}. A line at the foot says the stall last served {served_label(stats).lower()}.</desc>
  <defs>
    <filter id="grain" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" stitchTiles="stitch"/>
      <feColorMatrix type="saturate" values="0"/>
    </filter>
  </defs>
  <style>{STYLE}  </style>

  <rect class="sheet" width="{WIDTH}" height="{HEIGHT}" rx="{SHEET_R}"/>
  <path class="chit" d="M {CHIT_LEFT} {CHIT_TOP} H {CHIT_RIGHT} V {CHIT_BOTTOM} {torn_edge()} Z"/>

  <text x="{PAD_L}" y="54" class="soft mono meta">THE COUNTER &#183; KOPI O KOSONG BENG &#183; {stamp(stats["generated_on"])}</text>
  <path class="dot" d="M {PAD_L} 68 H {PAD_R}"/>

{rows()}

  <path class="dot" d="M {PAD_L} 372 H {PAD_R}"/>
  <text x="{PAD_L}" y="{FOOTER_Y}" class="soft mono eyebrow">LAST SERVED</text>
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
