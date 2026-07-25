# Kopi Order Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the signal lab GitHub profile with the Kopi Order design: a bilingual pair of READMEs fronted by a theme aware animated hawker stall signboard, guarded by tests that lock out badge walls, metrics, and job seeking copy.

**Architecture:** One Python generator holds the signboard geometry once and renders it twice, so the light and dark variants cannot drift apart. Both READMEs are hand written Markdown that share those two assets through a `<picture>` element. Two test modules split by responsibility: `test_signboard.py` guards the artwork and its generator, `test_profile.py` guards the copy in both languages.

**Tech Stack:** Python 3.14 standard library only (`string.Template`, `xml.etree.ElementTree`, `unittest`, `re`). No third party packages, no build step, no CI changes. SVG with CSS animation. GitHub flavoured Markdown.

Spec: [docs/superpowers/specs/2026-07-26-kopi-order-profile-design.md](../specs/2026-07-26-kopi-order-profile-design.md)

## Global Constraints

Every task's requirements implicitly include this section.

- **No dashes as punctuation** in any README copy. No em dash (`U+2014`), no en dash (`U+2013`), no hyphen used as a connector or aside. Hyphens survive only inside words genuinely spelled that way, such as `co-founder`.
- **Exactly one number** is permitted in either README: `18 m`. No other figure may appear.
- **Excluded metric strings:** `S$71K`, `71K`, `237`, `87.5`, `34%`, `16%`, `51%`, `4.57`, `18,000`.
- **Banned vocabulary:** passionate, leverage, seamless, robust, cutting edge, journey, showcase, delve, dive into, tapestry, realm, landscape, testament, elevate, unlock, empower, foster, dedicated, driven, enthusiast.
- **Banned job seeking phrases:** seeking, open to opportunit, available for, looking for a role, internship, hire me.
- **Banned widgets:** shields.io, skillicons, readme-typing-svg, github-readme-stats, streak-stats, github-profile-trophy, contribution graphs or snakes.
- **SVG output is pure ASCII.** Non ASCII characters are written as numeric entities so the files survive Windows encoding round trips. This repo has already been bitten twice, see commits `d2c414a` and `6544f13`.
- **Both SVGs share `viewBox="0 0 900 280"`** and identical geometry. Only colour tokens differ.
- **Every SVG carries** `role="img"`, `aria-labelledby`, a `<title>`, a `<desc>`, and a `prefers-reduced-motion: reduce` rule containing `animation: none !important`.
- **Links used throughout:** portfolio `https://zhifeng-portfolio.vercel.app/`, pitchMe `https://www.pitchmesg.com`, LinkedIn `https://www.linkedin.com/in/zhi-feng-chia-a50266210/`, email `mailto:zhifeng010729@gmail.com`.
- **Test command:** `python -m unittest discover -s tests -v` from the repository root.
- **Write every file with `encoding="utf-8"` and `newline="\n"`.**

## File Structure

| File | Responsibility |
|---|---|
| `scripts/generate_kopi_sign.py` | Holds signboard geometry once, renders both palettes. Sole source of the SVG assets. |
| `assets/kopi-sign-light.svg` | Generated. Cream paper variant. |
| `assets/kopi-sign-dark.svg` | Generated. Warm espresso variant. |
| `README.md` | English profile. This is what the GitHub profile page renders. |
| `README.zh.md` | Chinese profile, written as Chinese rather than translated. |
| `tests/test_signboard.py` | Guards artwork contract and generator reproducibility. |
| `tests/test_profile.py` | Guards copy contract across both languages. Rewritten from scratch. |
| `assets/signal-lab-*.svg`, `scripts/generate_signal_assets.py` | Deleted in Task 4. |

---

### Task 1: Signboard generator and assets

**Files:**
- Create: `scripts/generate_kopi_sign.py`
- Create: `tests/test_signboard.py`
- Generate: `assets/kopi-sign-light.svg`, `assets/kopi-sign-dark.svg`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: module `generate_kopi_sign` exposing `PALETTES: dict[str, dict[str, str]]` keyed `"light"` and `"dark"`, `render_svg(theme: str) -> str` returning the full ASCII SVG source, `to_ascii_entities(markup: str) -> str`, and `main() -> None` which writes `assets/kopi-sign-{theme}.svg`. Tasks 2 and 3 reference the asset paths `./assets/kopi-sign-dark.svg` and `./assets/kopi-sign-light.svg` from Markdown.

- [ ] **Step 1: Write the failing test**

Create `tests/test_signboard.py`:

```python
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_kopi_sign  # noqa: E402

ASSET_PATHS = {
    "dark": ROOT / "assets" / "kopi-sign-dark.svg",
    "light": ROOT / "assets" / "kopi-sign-light.svg",
}

REQUIRED_TEXT = (
    "KOPI O",
    "KOSONG BENG",
    "OPEN DAILY",
    "SINGAPORE",
    "咖啡乌",
    "无糖",
    "冰",
    "chia zhi feng",
    "谢梓峰",
)


class SignboardAssetTests(unittest.TestCase):
    def test_both_assets_exist_and_are_pure_ascii(self):
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                self.assertTrue(path.exists(), f"Missing {path}")
                source = path.read_text(encoding="utf-8")
                self.assertTrue(
                    source.startswith('<?xml version="1.0" encoding="UTF-8"?>\n')
                )
                self.assertTrue(source.isascii(), "SVG must be ASCII only")

    def test_assets_match_the_generator_exactly(self):
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                self.assertEqual(
                    path.read_text(encoding="utf-8"),
                    generate_kopi_sign.render_svg(theme),
                    "Asset has drifted from the generator. Re-run the script.",
                )

    def test_assets_share_geometry_and_accessibility_contract(self):
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                source = path.read_text(encoding="utf-8")
                root = ET.fromstring(source)
                self.assertEqual(root.attrib.get("viewBox"), "0 0 900 280")
                self.assertEqual(root.attrib.get("role"), "img")
                self.assertIn("aria-labelledby", root.attrib)
                self.assertIn("<title", source)
                self.assertIn("<desc", source)
                self.assertIn("prefers-reduced-motion: reduce", source)
                self.assertIn("animation: none !important", source)
                self.assertNotIn("<script", source.lower())
                self.assertNotIn("<image", source.lower())
                self.assertNotIn("@font-face", source)
                self.assertNotIn("xlink:href", source)
                self.assertNotIn("https://", source)

    def test_assets_carry_the_signboard_copy(self):
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                root = ET.fromstring(path.read_text(encoding="utf-8"))
                rendered = "".join(root.itertext())
                for label in REQUIRED_TEXT:
                    self.assertIn(label, rendered)

    def test_the_drink_is_iced_and_never_steaming(self):
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                source = path.read_text(encoding="utf-8")
                self.assertIn("class=\"ice\"", source)
                self.assertIn("drop motion", source)
                self.assertNotIn("steam", source.lower())

    def test_the_two_variants_differ_only_in_colour(self):
        light = ASSET_PATHS["light"].read_text(encoding="utf-8")
        dark = ASSET_PATHS["dark"].read_text(encoding="utf-8")
        self.assertNotEqual(light, dark)
        for theme in ("light", "dark"):
            for token in generate_kopi_sign.PALETTES[theme].values():
                self.assertIn(token, generate_kopi_sign.render_svg(theme))
        strip_light = light
        strip_dark = dark
        for key, value in generate_kopi_sign.PALETTES["light"].items():
            strip_light = strip_light.replace(value, f"${key}")
        for key, value in generate_kopi_sign.PALETTES["dark"].items():
            strip_dark = strip_dark.replace(value, f"${key}")
        self.assertEqual(strip_light, strip_dark)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest discover -s tests -p test_signboard.py -v`

Expected: FAIL at import with `ModuleNotFoundError: No module named 'generate_kopi_sign'`

- [ ] **Step 3: Write the generator**

Create `scripts/generate_kopi_sign.py`:

```python
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
```

- [ ] **Step 4: Generate the assets**

Run: `python scripts/generate_kopi_sign.py`

Expected: no output, exit code 0. Then confirm both files landed:

Run: `python -c "from pathlib import Path; [print(p.name, p.stat().st_size) for p in sorted(Path('assets').glob('kopi-sign-*.svg'))]"`

Expected: two lines, `kopi-sign-dark.svg` and `kopi-sign-light.svg`, each a few thousand bytes.

- [ ] **Step 5: Run the test to verify it passes**

Run: `python -m unittest discover -s tests -p test_signboard.py -v`

Expected: `Ran 6 tests`, `OK`

- [ ] **Step 6: Eyeball the artwork in a browser**

Open both files and confirm: nothing clips, the wordmark and glass do not collide, the drink reads as iced rather than hot, the droplets slide slowly, and the dark variant is warm rather than blue.

Run: `python -c "import webbrowser, pathlib; [webbrowser.open(pathlib.Path(p).resolve().as_uri()) for p in ['assets/kopi-sign-light.svg','assets/kopi-sign-dark.svg']]"`

If anything looks wrong, adjust coordinates in the template, re-run Step 4, then Step 5.

- [ ] **Step 7: Commit**

```bash
git add scripts/generate_kopi_sign.py tests/test_signboard.py assets/kopi-sign-light.svg assets/kopi-sign-dark.svg
git commit -m "feat: add kopi signboard artwork and generator"
```

---

### Task 2: English README and the shared copy contract

**Files:**
- Modify: `README.md` (full replacement of all 39 lines)
- Rewrite: `tests/test_profile.py` (full replacement of all 116 lines)

**Interfaces:**
- Consumes: `./assets/kopi-sign-dark.svg` and `./assets/kopi-sign-light.svg` from Task 1.
- Produces: `tests/test_profile.py` defining module constants `BANNED_WIDGETS`, `BANNED_JOB_SEEKING`, `BANNED_METRICS`, `BANNED_VOCAB`, `LINKS`, and a `ProfileCopyTests.assert_shared_contract(self, text: str, label: str) -> None` helper. Task 3 calls that helper against `README.zh.md`, so do not rename it.

- [ ] **Step 1: Write the failing test**

Replace the entire contents of `tests/test_profile.py`:

```python
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
README_EN = ROOT / "README.md"

BANNED_WIDGETS = (
    "shields.io",
    "skillicons",
    "readme-typing-svg",
    "github-readme-stats",
    "streak-stats",
    "github-profile-trophy",
    "contribution-graph",
    "contribution-snake",
    "snk.svg",
)

BANNED_JOB_SEEKING = (
    "seeking",
    "open to opportunit",
    "available for",
    "looking for a role",
    "internship",
    "hire me",
)

BANNED_METRICS = (
    "S$71K",
    "71K",
    "237",
    "87.5",
    "34%",
    "16%",
    "51%",
    "4.57",
    "18,000",
)

BANNED_VOCAB = (
    "passionate",
    "leverage",
    "seamless",
    "robust",
    "cutting edge",
    "journey",
    "showcase",
    "delve",
    "dive into",
    "tapestry",
    "realm",
    "landscape",
    "testament",
    "elevate",
    "unlock",
    "empower",
    "foster",
    "dedicated",
    "driven",
    "enthusiast",
)

LINKS = (
    "https://zhifeng-portfolio.vercel.app/",
    "https://www.pitchmesg.com",
    "https://www.linkedin.com/in/zhi-feng-chia-a50266210/",
    "mailto:zhifeng010729@gmail.com",
)

MOJIBAKE = ("Â·", "â€”", "ï¿½")


class ProfileCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.english = README_EN.read_text(encoding="utf-8")

    @staticmethod
    def prose_only(text):
        """Strip link targets and HTML attribute values.

        The digit scan must read prose, not addresses. Without this the email
        zhifeng010729@gmail.com and the LinkedIn slug a50266210 both look like
        stray metrics.
        """
        stripped = re.sub(r"\]\([^)]*\)", "]", text)
        return re.sub(r'[\w-]+="[^"]*"', "", stripped)

    def assert_shared_contract(self, text, label):
        """Every rule that applies to both language files."""
        with self.subTest(check="theme aware signboard", file=label):
            self.assertIn("<picture>", text)
            self.assertIn('media="(prefers-color-scheme: dark)"', text)
            self.assertIn('media="(prefers-color-scheme: light)"', text)
            self.assertIn("./assets/kopi-sign-dark.svg", text)
            self.assertIn("./assets/kopi-sign-light.svg", text)
            self.assertIn('width="100%"', text)

        with self.subTest(check="image has alt text", file=label):
            self.assertRegex(text, r'<img alt="[^"]{20,}"')

        with self.subTest(check="only the diving depth", file=label):
            numbers = set(re.findall(r"\d+", self.prose_only(text)))
            self.assertTrue(
                numbers <= {"18"},
                f"Unexpected numbers in {label}: {sorted(numbers - {'18'})}",
            )

        with self.subTest(check="no slop widgets", file=label):
            for widget in BANNED_WIDGETS:
                self.assertNotIn(widget, text.lower())

        with self.subTest(check="no job seeking", file=label):
            for phrase in BANNED_JOB_SEEKING:
                self.assertNotIn(phrase, text.lower())

        with self.subTest(check="no metrics", file=label):
            for metric in BANNED_METRICS:
                self.assertNotIn(metric, text)

        with self.subTest(check="no dashes as punctuation", file=label):
            self.assertNotIn("—", text)
            self.assertNotIn("–", text)

        with self.subTest(check="no banned vocabulary", file=label):
            for entry in BANNED_VOCAB:
                pattern = r"\b" + re.escape(entry) + r"\b"
                self.assertIsNone(
                    re.search(pattern, text, flags=re.IGNORECASE),
                    f"{label} contains banned wording: {entry}",
                )

        with self.subTest(check="links present", file=label):
            for link in LINKS:
                self.assertIn(link, text)

        with self.subTest(check="exactly two easter eggs", file=label):
            self.assertEqual(text.count("<details>"), 2)
            self.assertEqual(text.count("</details>"), 2)

        with self.subTest(check="no mojibake", file=label):
            for garbled in MOJIBAKE:
                self.assertNotIn(garbled, text)

    def test_english_readme_meets_the_shared_contract(self):
        self.assert_shared_contract(self.english, "README.md")

    def test_english_readme_carries_the_menu_sections(self):
        for heading in ("NOW SERVING", "ON THE SIDE", "ALSO IN THE CUP"):
            self.assertIn(heading, self.english)

    def test_english_readme_leads_with_pitchme(self):
        serving = self.english.index("NOW SERVING")
        side = self.english.index("ON THE SIDE")
        self.assertIn("pitchMe", self.english[serving:side])
        self.assertIn("co-founder and CTO", self.english[serving:side])

    def test_english_readme_closes_with_the_signature(self):
        self.assertIn("no sugar. never was.", self.english)

    def test_english_readme_does_not_restore_the_signal_lab(self):
        for phrase in ("signal-lab", "SIGNAL LAB", "CODE · CIRCUITS · COFFEE"):
            self.assertNotIn(phrase, self.english)


if __name__ == "__main__":
    unittest.main()
```

Note on the `only the diving depth` subtest: it scans every digit run in the prose and allows exactly one, the `18` of `18 m`. This is the strongest guard in the module, because `BANNED_METRICS` only catches metrics pasted verbatim while this catches one arriving inside a reworded sentence. It runs through `prose_only` first, since the email address and the LinkedIn slug both contain long digit runs that are addresses rather than claims. It lives in the shared contract so it covers the Chinese file too once Task 3 lands.

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest discover -s tests -p test_profile.py -v`

Expected: FAIL. `test_english_readme_meets_the_shared_contract` fails first on the missing `./assets/kopi-sign-dark.svg`, since `README.md` still points at the signal lab assets.

- [ ] **Step 3: Write the English README**

Replace the entire contents of `README.md`:

```markdown
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/kopi-sign-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/kopi-sign-light.svg">
  <img alt="A hawker stall signboard reading Kopi O Kosong Beng, with a glass of iced black coffee beside it" src="./assets/kopi-sign-light.svg" width="100%">
</picture>

<p align="center">
  English &nbsp;&middot;&nbsp; <a href="./README.zh.md">中文</a>
</p>

I'm Zhi Feng. I study Computer Science and Design at SUTD. Most of what I build has to deal with the physical world at some point, and that is where the interesting bugs live.

### NOW SERVING

**[pitchMe](https://www.pitchmesg.com)**, co-founder and CTO. It's an AI speaking coach. You record yourself talking and it tells you the truth about it. Schools and youth programmes around Singapore use it.

### ON THE SIDE

* a robot arm I taught to pick things up without dropping them
* a two player math game with no CPU in it, just wires and states
* quantum devices, in a cleanroom, at hours I would rather not say
* a very stubborn dataset about American carbon emissions

### ALSO IN THE CUP

* taekwondo. I competed. I was bad at first.
* certified to go 18 m down, where there is no signal, which is the point
* marathons and mountains, mostly for the view
* table tennis, undefeated (sample size: my friends)

### THE FULL MENU

[Portfolio](https://zhifeng-portfolio.vercel.app/) &nbsp;&middot;&nbsp; [pitchMe](https://www.pitchmesg.com) &nbsp;&middot;&nbsp; [LinkedIn](https://www.linkedin.com/in/zhi-feng-chia-a50266210/) &nbsp;&middot;&nbsp; [say hi](mailto:zhifeng010729@gmail.com)

<details>
<summary>why kopi o kosong beng?</summary>
<br>

It's my order. Kopi is coffee, o means no milk, kosong means no sugar, beng means iced. So: iced black coffee, unsweetened.

And yes, the glass on the sign up there has ice in it. That was on purpose.

</details>

<details>
<summary>what's brewing</summary>
<br>

Still at SUTD. Flying to Waterloo at the end of August for an exchange semester. Right now I'm building my portfolio site, which is the one place I let myself write things down properly.

</details>

<p align="center"><i>no sugar. never was.</i></p>
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest discover -s tests -p test_profile.py -v`

Expected: `Ran 5 tests`, `OK`

- [ ] **Step 5: Confirm the file is clean UTF-8 with no stray dashes**

Run: `python -c "src=open('README.md',encoding='utf-8').read(); print('non-ascii:', sorted({c for c in src if ord(c)>127})); print('dashes:', [c for c in src if c in '—–'])"`

Expected: `non-ascii:` lists only `·`, `中`, `文`. `dashes: []`

- [ ] **Step 6: Commit**

```bash
git add README.md tests/test_profile.py
git commit -m "feat: rewrite profile README as the kopi order menu"
```

---

### Task 3: Chinese README and the language switch

**Files:**
- Create: `README.zh.md`
- Modify: `tests/test_profile.py` (add the Chinese constant, three tests, and extend `setUpClass`)

**Interfaces:**
- Consumes: `ProfileCopyTests.assert_shared_contract(self, text, label)` and the `LINKS` constant from Task 2. The same two SVG assets from Task 1.
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Write the failing test**

In `tests/test_profile.py`, add the path constant directly beneath `README_EN`:

```python
README_ZH = ROOT / "README.zh.md"
```

Replace the existing `setUpClass` with:

```python
    @classmethod
    def setUpClass(cls):
        cls.english = README_EN.read_text(encoding="utf-8")
        cls.chinese = README_ZH.read_text(encoding="utf-8")
```

Add these three tests directly above the `if __name__ == "__main__":` block:

```python
    def test_chinese_readme_meets_the_shared_contract(self):
        self.assert_shared_contract(self.chinese, "README.zh.md")

    def test_chinese_readme_carries_the_menu_sections(self):
        for heading in ("今日供应", "配菜", "杯里还有"):
            self.assertIn(heading, self.chinese)
        self.assertIn("pitchMe", self.chinese)
        self.assertIn("不要糖。从来都不要。", self.chinese)

    def test_the_language_switch_works_in_both_directions(self):
        self.assertIn('href="./README.zh.md"', self.english)
        self.assertIn("中文", self.english)
        self.assertIn('href="./README.md"', self.chinese)
        self.assertIn(">English</a>", self.chinese)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest discover -s tests -p test_profile.py -v`

Expected: ERROR in `setUpClass` with `FileNotFoundError` for `README.zh.md`.

- [ ] **Step 3: Write the Chinese README**

Create `README.zh.md`:

```markdown
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/kopi-sign-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/kopi-sign-light.svg">
  <img alt="写着 Kopi O Kosong Beng 的咖啡摊招牌,旁边是一杯冰咖啡乌" src="./assets/kopi-sign-light.svg" width="100%">
</picture>

<p align="center">
  <a href="./README.md">English</a> &nbsp;&middot;&nbsp; 中文
</p>

我是谢梓峰,在 SUTD 读计算机科学与设计。我做的东西多半最后都要碰到实体世界,有意思的 bug 都藏在那里。

### 今日供应

**[pitchMe](https://www.pitchmesg.com)**,co-founder 兼 CTO。用 AI 教你讲话:你录一段自己说话的视频,它老实告诉你讲得怎么样。新加坡的一些学校和青年计划在用。

### 配菜

* 一只被我教会不把东西摔在地上的机械臂
* 一个双人数学游戏,里面没有 CPU,只有线和状态
* 无尘室里的量子元件,几点做的就不说了
* 一份很不听话的美国碳排放数据

### 杯里还有

* 跆拳道。比过赛。一开始打得很烂。
* 潜水执照,最深 18 米,下面没有信号,这正是重点
* 马拉松和爬山,主要是为了看风景
* 乒乓球至今不败(样本:我的朋友)

### 完整菜单

[作品集](https://zhifeng-portfolio.vercel.app/) &nbsp;&middot;&nbsp; [pitchMe](https://www.pitchmesg.com) &nbsp;&middot;&nbsp; [LinkedIn](https://www.linkedin.com/in/zhi-feng-chia-a50266210/) &nbsp;&middot;&nbsp; [打个招呼](mailto:zhifeng010729@gmail.com)

<details>
<summary>为什么叫 kopi o kosong beng?</summary>
<br>

这就是我每次点的。Kopi 是咖啡,o 是不加奶,kosong 是不加糖,beng 是加冰。合起来:冰咖啡乌,不甜。

对,上面招牌里那杯是有冰的。故意的。

</details>

<details>
<summary>最近在煮什么</summary>
<br>

还在 SUTD。八月底飞去 Waterloo 交换一个学期。现在主要在做自己的作品集网站,那是我唯一会好好把东西写下来的地方。

</details>

<p align="center"><i>不要糖。从来都不要。</i></p>
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest discover -s tests -p test_profile.py -v`

Expected: `Ran 8 tests`, `OK`

- [ ] **Step 5: Confirm the Chinese file has no full width dashes**

Chinese typography often reaches for `——`, which the no dashes rule forbids.

Run: `python -c "src=open('README.zh.md',encoding='utf-8').read(); print('dashes:', [c for c in src if c in '—–―－'])"`

Expected: `dashes: []`

- [ ] **Step 6: Commit**

```bash
git add README.zh.md tests/test_profile.py
git commit -m "feat: add Chinese profile and language switch"
```

---

### Task 4: Remove the superseded signal lab and verify the whole profile

**Files:**
- Delete: `assets/signal-lab-dark.svg`, `assets/signal-lab-light.svg`, `scripts/generate_signal_assets.py`
- Modify: `tests/test_signboard.py` (add one test)

**Interfaces:**
- Consumes: everything from Tasks 1 through 3.
- Produces: nothing.

- [ ] **Step 1: Write the failing test**

In `tests/test_signboard.py`, add this test to `SignboardAssetTests`, directly above the `if __name__ == "__main__":` block:

```python
    def test_the_signal_lab_is_gone_for_good(self):
        stale = (
            ROOT / "assets" / "signal-lab-dark.svg",
            ROOT / "assets" / "signal-lab-light.svg",
            ROOT / "scripts" / "generate_signal_assets.py",
        )
        for path in stale:
            with self.subTest(path=path.name):
                self.assertFalse(
                    path.exists(),
                    f"{path.name} was superseded by the kopi signboard and must not return.",
                )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest discover -s tests -p test_signboard.py -v`

Expected: FAIL on `test_the_signal_lab_is_gone_for_good` with three subTest failures, one per stale file.

- [ ] **Step 3: Delete the superseded files**

```bash
git rm assets/signal-lab-dark.svg assets/signal-lab-light.svg scripts/generate_signal_assets.py
```

- [ ] **Step 4: Run the full suite to verify everything passes**

Run: `python -m unittest discover -s tests -v`

Expected: `Ran 15 tests`, `OK`

- [ ] **Step 5: Verify the working tree is clean and the diff is scoped**

Run: `git diff --check`

Expected: no output.

Run: `git status --short`

Expected: only the three staged deletions from Step 3.

- [ ] **Step 6: Verify every link resolves**

Run: `python -c "import urllib.request as u; [print(l, u.urlopen(u.Request(l, headers={'User-Agent':'Mozilla/5.0'}), timeout=15).status) for l in ['https://zhifeng-portfolio.vercel.app/','https://www.pitchmesg.com','https://www.linkedin.com/in/zhi-feng-chia-a50266210/']]"`

Expected: `200` for the portfolio and pitchMe. LinkedIn commonly answers `999` or `403` to non browser clients, which is not a broken link. Only investigate a `404`.

- [ ] **Step 7: Cold read both READMEs**

Read `README.md` and `README.zh.md` end to end. Reject any sentence that sounds machine written. Specifically check: no balanced triplets, no sentence that restates the one before it, uneven sentence lengths, and no dash doing the work a full stop should do.

- [ ] **Step 8: Commit**

```bash
git add tests/test_signboard.py
git commit -m "chore: retire the signal lab profile assets"
```

---

## Verification against the spec

Run through this list before declaring the plan complete. Each line maps to the spec's Verification section.

1. `python -m unittest discover -s tests -v` reports `Ran 15 tests`, `OK`.
2. Both SVG variants render without clipping at desktop and narrow widths in both GitHub themes. Check by pushing to a branch and viewing the rendered README, or by resizing a browser window on the raw SVG files.
3. Reduced motion yields a complete static signboard. Check in Chrome DevTools with Rendering, Emulate CSS prefers-reduced-motion: reduce.
4. Every link in both READMEs resolves. Covered by Task 4 Step 6.
5. The language switch works in both directions on GitHub. Only verifiable after push, since relative Markdown links resolve against the repository.
6. Markdown and HTML nesting is valid for GitHub's renderer. The `<details>` blocks each keep a blank line after `<br>` so the Markdown inside them renders.
7. `git diff --check` reports no whitespace errors. Covered by Task 4 Step 5.
8. The final diff touches only: `README.md`, `README.zh.md`, `assets/kopi-sign-*.svg`, `scripts/generate_kopi_sign.py`, `tests/test_profile.py`, `tests/test_signboard.py`, and the three deletions.
9. A cold read finds no machine written sentence. Covered by Task 4 Step 7.

## Post implementation, for ZF by hand

These are out of scope for the plan and cannot be done from the repository. They are listed so they are not forgotten.

- Push the branch and confirm the profile page renders as expected at `https://github.com/Kopi-O-Kosong-Beng`.
- The GitHub bio field, website field, and pinned repositories are untouched by this plan and still say what they said before.
