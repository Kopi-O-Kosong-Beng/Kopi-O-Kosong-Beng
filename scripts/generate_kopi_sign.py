from pathlib import Path
from string import Template


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"

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
        "ink_soft": "#8B6F55",
        "accent": "#C2703A",
        "rule": "#D9C3A5",
        "coffee": "#4A2C17",
        "ice": "#E8F1F3",
        "ice_line": "#AFC6CC",
        "glass": "#93A9AF",
    },
}

SVG_TEMPLATE = Template("""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 280" role="img" aria-labelledby="title desc">
  <title id="title">Kopi O Kosong Beng, the stall sign of Chia Zhi Feng</title>
  <desc id="desc">A hawker stall signboard reading Kopi O Kosong Beng above the name Chia Zhi Feng, with a tall glass of iced black coffee standing beside it.</desc>
  <style>
    text { font-family: Georgia, "Iowan Old Style", "Palatino Linotype", "Times New Roman", serif; }
    .ink { fill: $ink; }
    .soft { fill: $ink_soft; }
    .board { fill: $panel; stroke: $rule; stroke-width: 2; }
    .board-inner { fill: none; stroke: $rule; stroke-width: 1; }
    .rule { fill: none; stroke: $rule; stroke-width: 1; }
    .kicker { font-size: 12px; letter-spacing: 5px; }
    .word { font-size: 52px; font-weight: 700; letter-spacing: 3px; }
    .zh { font-size: 15px; letter-spacing: 4px; }
    .name { font-size: 16px; letter-spacing: 2.4px; }
    .glass { fill: none; stroke: $glass; stroke-width: 2.4; stroke-linejoin: round; }
    .brew { fill: $coffee; }
    .ice { fill: $ice; opacity: 0.92; }
    .ice-edge { fill: none; stroke: $ice_line; stroke-width: 1; }
    .straw { fill: none; stroke: $accent; stroke-width: 4; stroke-linecap: round; }
    .drop { fill: $ice; opacity: 0; }
    .drop-a { animation: bead 5s ease-in 0s infinite; }
    .drop-b { animation: bead 5s ease-in 1.7s infinite; }
    .drop-c { animation: bead 5s ease-in 3.4s infinite; }
    @keyframes bead {
      0% { transform: translateY(0px); opacity: 0; }
      12% { opacity: 0.85; }
      70% { opacity: 0.7; }
      100% { transform: translateY(56px); opacity: 0; }
    }
    @media (prefers-reduced-motion: reduce) {
      .motion { animation: none !important; opacity: 0.7 !important; }
    }
  </style>

  <rect width="900" height="280" rx="14" fill="$paper"/>
  <rect class="board" x="22" y="20" width="856" height="240" rx="10"/>
  <rect class="board-inner" x="34" y="32" width="832" height="216" rx="6"/>

  <text x="90" y="62" class="soft kicker">OPEN DAILY &#183; SINGAPORE</text>
  <path class="rule" d="M 90 74 H 520"/>

  <text x="90" y="132" class="ink word">KOPI O</text>
  <text x="90" y="184" class="ink word">KOSONG BENG</text>
  <text x="90" y="212" class="soft zh">&#21654;&#21857;&#20044; &#183; &#26080;&#31958; &#183; &#20912;</text>
  <text x="92" y="238" class="ink name">chia zhi feng &#183; &#35874;&#26771;&#23792;</text>

  <path class="rule" d="M 620 60 V 240"/>

  <g aria-label="A glass of iced kopi">
    <path class="brew" d="M 717 98 L 724 226 Q 726 234 734 234 L 766 234 Q 774 234 776 226 L 783 98 Z"/>
    <ellipse class="brew" cx="750" cy="98" rx="33" ry="7"/>
    <rect class="ice" x="728" y="94" width="20" height="20" rx="3" transform="rotate(-14 738 104)"/>
    <rect class="ice-edge" x="728" y="94" width="20" height="20" rx="3" transform="rotate(-14 738 104)"/>
    <rect class="ice" x="752" y="102" width="18" height="18" rx="3" transform="rotate(11 761 111)"/>
    <rect class="ice-edge" x="752" y="102" width="18" height="18" rx="3" transform="rotate(11 761 111)"/>
    <rect class="ice" x="736" y="120" width="17" height="17" rx="3" transform="rotate(6 744 128)"/>
    <rect class="ice-edge" x="736" y="120" width="17" height="17" rx="3" transform="rotate(6 744 128)"/>
    <path class="straw" d="M 766 56 L 742 150"/>
    <path class="glass" d="M 714 74 L 724 226 Q 726 234 734 234 L 766 234 Q 774 234 776 226 L 786 74"/>
    <ellipse class="glass" cx="750" cy="74" rx="36" ry="8"/>
    <ellipse class="drop motion drop-a" cx="720" cy="118" rx="3" ry="4"/>
    <ellipse class="drop motion drop-b" cx="780" cy="136" rx="2.6" ry="3.6"/>
    <ellipse class="drop motion drop-c" cx="724" cy="158" rx="2.4" ry="3.2"/>
    <path class="rule" d="M 702 244 H 798"/>
  </g>
</svg>
""")


def to_ascii_entities(markup: str) -> str:
    return "".join(ch if ord(ch) < 128 else f"&#{ord(ch)};" for ch in markup)


def render_svg(theme: str) -> str:
    return to_ascii_entities(SVG_TEMPLATE.substitute(PALETTES[theme]))


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for theme in PALETTES:
        target = ASSET_DIR / f"kopi-sign-{theme}.svg"
        with target.open("w", encoding="utf-8", newline="\n") as asset:
            asset.write(render_svg(theme))


if __name__ == "__main__":
    main()
