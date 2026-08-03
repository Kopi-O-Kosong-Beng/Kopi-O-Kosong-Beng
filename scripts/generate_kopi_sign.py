from pathlib import Path
from string import Template


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"

# The stack is curated, not detected. Only three public repos exist and their
# languages read as Python, Python and null, so anything auto-detected would be
# a lie by omission. Both cards read this tuple: the signboard prints the full
# names along its specials strip, the chit stamps the short labels onto ice
# cubes. Keeping one tuple stops the two lists from drifting apart.
STACK = (
    ("python", "py"),
    ("c++", "c++"),
    ("typescript", "ts"),
    ("ros", "ros"),
    ("fpga", "fpga"),
    ("gcp", "gcp"),
)

STACK_LINE = " · ".join(name for name, _ in STACK)

PALETTES = {
    "dark": {
        "paper": "#100D0A",
        "panel": "#1B1611",
        "ink": "#F2E5D1",
        "ink_soft": "#A78D70",
        "accent": "#E09551",
        "rule": "#3B2F23",
        "coffee": "#3A2211",
        "ice": "#DCE9EC",
        "ice_line": "#7E969C",
        "glass": "#6F8389",
    },
    "light": {
        "paper": "#F2E7D5",
        "panel": "#FBF4E7",
        "ink": "#3A2214",
        "ink_soft": "#816548",
        "accent": "#C2703A",
        "rule": "#D9C3A5",
        "coffee": "#4A2C17",
        "ice": "#E8F1F3",
        "ice_line": "#AFC6CC",
        "glass": "#71878E",
    },
}

SVG_TEMPLATE = Template("""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 280" role="img" aria-labelledby="title desc">
  <title id="title">Kopi O Kosong Beng, the stall sign of Chia Zhi Feng</title>
  <desc id="desc">A hawker stall signboard reading Kopi O Kosong Beng above the name Chia Zhi Feng, with a tall glass of iced black coffee standing beside it. A specials strip along the bottom is headed Today's Brew and lists python, C++, TypeScript, ROS, FPGA and GCP.</desc>
  <style>
    text { font-family: Georgia, "Iowan Old Style", "Palatino Linotype", "Times New Roman", serif; }
    .ink { fill: $ink; }
    .soft { fill: $ink_soft; }
    .board { fill: $panel; stroke: $rule; stroke-width: 2; }
    .board-inner { fill: none; stroke: $rule; stroke-width: 1; }
    .rule { fill: none; stroke: $rule; stroke-width: 1; }
    .kicker { font-size: 11px; letter-spacing: 5px; }
    .word { font-size: 44px; font-weight: 700; letter-spacing: 3px; }
    .zh { font-size: 13px; letter-spacing: 4px; }
    .name { font-size: 14px; letter-spacing: 2.4px; }
    .label { font-size: 9px; letter-spacing: 3px; }
    .stack {
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 13px;
      letter-spacing: 0.6px;
    }
    .glass { fill: none; stroke: $glass; stroke-width: 2.4; stroke-linejoin: round; }
    .brew { fill: $coffee; }
    .ice { fill: $ice; fill-opacity: 0.92; stroke: $ice_line; stroke-width: 1; }
    .straw { fill: none; stroke: $accent; stroke-width: 4; stroke-linecap: round; }
    .drop { fill: $ice; opacity: 0; }
    .drop-a { animation: bead 5s ease-in 0s infinite; }
    .drop-b { animation: bead 5s ease-in 1.7s infinite; }
    .drop-c { animation: bead 5s ease-in 3.4s infinite; }
    @keyframes bead {
      0% { transform: translateY(0px); opacity: 0; }
      12% { opacity: 0.85; }
      70% { opacity: 0.7; }
      100% { transform: translateY(40px); opacity: 0; }
    }
    @media (prefers-reduced-motion: reduce) {
      .motion { animation: none !important; opacity: 0.7 !important; }
    }
  </style>

  <rect width="900" height="280" rx="14" fill="$paper"/>
  <rect class="board" x="22" y="20" width="856" height="240" rx="10"/>
  <rect class="board-inner" x="34" y="32" width="832" height="216" rx="6"/>

  <text x="90" y="56" class="soft kicker">OPEN DAILY &#183; SINGAPORE</text>

  <text x="90" y="106" class="ink word">KOPI O</text>
  <text x="90" y="150" class="ink word">KOSONG BENG</text>
  <text x="90" y="172" class="soft zh">&#21654;&#21857;&#20044; &#183; &#26080;&#31958; &#183; &#20912;</text>
  <text x="92" y="194" class="ink name">chia zhi feng &#183; &#35874;&#26771;&#23792;</text>

  <path class="rule" d="M 620 44 V 196"/>

  <g aria-label="A glass of iced kopi">
    <path class="brew" d="M 733 80 L 738 188 Q 740 196 747 196 L 773 196 Q 780 196 782 188 L 787 80 Z"/>
    <ellipse class="brew" cx="760" cy="80" rx="27" ry="6"/>
    <rect class="ice" x="741" y="78" width="17" height="17" rx="3" transform="rotate(-14 749 86)"/>
    <rect class="ice" x="760" y="86" width="15" height="15" rx="3" transform="rotate(11 767 93)"/>
    <rect class="ice" x="746" y="100" width="14" height="14" rx="3" transform="rotate(6 753 107)"/>
    <path class="straw" d="M 776 44 L 754 116"/>
    <path class="glass" d="M 730 58 L 738 188 Q 740 196 747 196 L 773 196 Q 780 196 782 188 L 790 58"/>
    <ellipse class="glass" cx="760" cy="58" rx="30" ry="7"/>
    <ellipse class="drop motion drop-a" cx="734" cy="96" rx="2.8" ry="3.8"/>
    <ellipse class="drop motion drop-b" cx="786" cy="110" rx="2.4" ry="3.4"/>
    <ellipse class="drop motion drop-c" cx="737" cy="128" rx="2.2" ry="3"/>
  </g>

  <path class="rule" d="M 90 212 H 810"/>
  <text x="90" y="236" class="soft label">TODAY&#39;S BREW</text>
  <text x="214" y="236" class="ink stack">$stack_line</text>
</svg>
""")


def to_ascii_entities(markup: str) -> str:
    return "".join(ch if ord(ch) < 128 else f"&#{ord(ch)};" for ch in markup)


def render_svg(theme: str) -> str:
    # Substitution runs first so the interpolated middot in STACK_LINE still
    # gets folded into a numeric entity by to_ascii_entities.
    return to_ascii_entities(
        SVG_TEMPLATE.substitute(stack_line=STACK_LINE, **PALETTES[theme])
    )


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for theme in PALETTES:
        target = ASSET_DIR / f"kopi-sign-{theme}.svg"
        with target.open("w", encoding="utf-8", newline="\n") as asset:
            asset.write(render_svg(theme))


if __name__ == "__main__":
    main()
