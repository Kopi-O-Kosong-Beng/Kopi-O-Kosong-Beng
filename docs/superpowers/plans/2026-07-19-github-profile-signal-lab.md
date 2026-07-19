# GitHub Profile Signal Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current project-heavy profile README with a short GitHub-native profile centred on a self-hosted animated Signal Lab SVG.

**Architecture:** The README selects one of two standalone SVG assets through a theme-aware `<picture>` element. A Python standard-library test records the required copy, links, native details elements, SVG structure, accessibility metadata, motion fallback, and forbidden legacy language. The main visual has no external runtime or third-party rendering dependency.

**Tech Stack:** GitHub Markdown, HTML `<picture>` and `<details>`, SVG 1.1, SVG CSS animations, Python 3 `unittest`, Playwright for visual verification

## Global Constraints

- Do not include ChatGPT, Codex, AI tools, or any AI system as a commit co-author.
- Do not use the em dash character `—` anywhere in README copy or SVG text.
- Avoid marketing language and familiar AI phrases. Use the exact approved copy in this plan.
- The profile is a creative GitHub signature. It is not a résumé, portfolio duplicate, startup pitch, or job advertisement.
- Do not include project tables, skill walls, GitHub statistics cards, contribution graphs, startup metrics, or job availability.
- Keep the main experience self-hosted in this repository.
- Provide separate `900 × 300` light and dark SVG assets with identical geometry.
- Honour `prefers-reduced-motion: reduce` and retain a complete static composition.
- Keep exactly two native GitHub `<details>` Easter eggs.
- Every implementation commit must use Zhi Feng as the sole author and contain no co-author trailer.

---

### Task 1: Implement and verify the complete Signal Lab profile

**Files:**
- Create: `tests/test_profile.py`
- Create: `scripts/generate_signal_assets.py`
- Create: `assets/signal-lab-dark.svg`
- Create: `assets/signal-lab-light.svg`
- Modify: `README.md`

**Interfaces:**
- Consumes: the approved design in `docs/superpowers/specs/2026-07-19-github-profile-signal-lab-design.md`
- Produces: a theme-aware GitHub profile README, two self-contained SVG assets, and a reusable validation test

- [ ] **Step 1: Write the failing profile contract test**

Create `tests/test_profile.py` with this complete content:

```python
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
ASSET_PATHS = {
    "dark": ROOT / "assets" / "signal-lab-dark.svg",
    "light": ROOT / "assets" / "signal-lab-light.svg",
}


class ProfileReadmeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = README_PATH.read_text(encoding="utf-8")

    def test_readme_uses_theme_aware_signal_lab_assets(self):
        self.assertIn("<picture>", self.readme)
        self.assertIn('media="(prefers-color-scheme: dark)"', self.readme)
        self.assertIn("./assets/signal-lab-dark.svg", self.readme)
        self.assertIn("./assets/signal-lab-light.svg", self.readme)
        self.assertIn('width="100%"', self.readme)

    def test_readme_uses_approved_identity_copy_and_links(self):
        expected_copy = (
            "I study Computer Science and Design at SUTD. I like building "
            "things that connect software to the physical world."
        )
        self.assertIn(expected_copy, self.readme)
        self.assertIn("https://zhifeng-portfolio.vercel.app/", self.readme)
        self.assertIn(
            "https://www.linkedin.com/in/zhi-feng-chia-a50266210/",
            self.readme,
        )
        self.assertIn("mailto:zhifeng010729@gmail.com", self.readme)

    def test_readme_has_exactly_two_native_easter_eggs(self):
        self.assertEqual(self.readme.count("<details>"), 2)
        self.assertEqual(self.readme.count("</details>"), 2)
        self.assertIn("brew --profile", self.readme)
        self.assertIn("why the username?", self.readme)
        self.assertIn("kopi o kosong", self.readme.lower())

    def test_readme_does_not_restore_legacy_marketing_content(self):
        forbidden = (
            "survive real users",
            "I run engineering at",
            "S$71K",
            "Selected builds",
            "Tools I reach for",
            "Co-founder",
            "open to internships",
            "ChatGPT",
            "Codex",
            "—",
        )
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, self.readme)

    def test_svg_assets_follow_the_shared_contract(self):
        required_text = (
            "CHIA ZHI FENG",
            "谢梓峰",
            "CODE · CIRCUITS · COFFEE",
            "AI / ML",
            "BACKEND",
            "ROBOTS",
            "FPGA",
            "01°17′N / 103°51′E",
            "SIGNAL ONLINE",
        )

        for theme, asset_path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                self.assertTrue(asset_path.exists(), f"Missing {asset_path}")
                source = asset_path.read_text(encoding="utf-8")
                root = ET.fromstring(source)
                self.assertEqual(root.attrib.get("viewBox"), "0 0 900 300")
                self.assertEqual(root.attrib.get("role"), "img")
                self.assertIn("aria-labelledby", root.attrib)
                self.assertIn("<title", source)
                self.assertIn("<desc", source)
                self.assertIn("prefers-reduced-motion: reduce", source)
                self.assertIn("animation: none !important", source)
                self.assertNotIn("<script", source.lower())
                self.assertNotIn("<image", source.lower())
                for label in required_text:
                    self.assertIn(label, source)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the contract test and confirm the expected failure**

Run:

```powershell
python -m unittest -v tests/test_profile.py
```

Expected: failures for the missing theme-aware `<picture>` markup and missing SVG assets. The test must load successfully and fail because the new profile has not been implemented.

- [ ] **Step 3: Create the complete asset generator and produce both SVG files**

Create `scripts/generate_signal_assets.py` with this complete content:

```python
from pathlib import Path
from string import Template


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"

PALETTES = {
    "dark": {
        "background": "#08151D",
        "grid": "#17313C",
        "primary": "#EEF8FA",
        "secondary": "#7894A0",
        "signal": "#68DCC9",
        "line": "#2E6977",
        "node_fill": "#0E222C",
        "node_border": "#347687",
    },
    "light": {
        "background": "#F5F3EC",
        "grid": "#D9DED9",
        "primary": "#13262E",
        "secondary": "#65767A",
        "signal": "#087F73",
        "line": "#79A7A5",
        "node_fill": "#E9F1ED",
        "node_border": "#4D918C",
    },
}

SVG_TEMPLATE = Template("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 300" role="img" aria-labelledby="title desc">
  <title id="title">Chia Zhi Feng Signal Lab</title>
  <desc id="desc">An animated engineering schematic connecting coffee with AI, backend systems, robots, and FPGA hardware.</desc>
  <defs>
    <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
      <path d="M 24 0 L 0 0 0 24" fill="none" stroke="$grid" stroke-width="1"/>
    </pattern>
    <filter id="glow" x="-200%" y="-200%" width="500%" height="500%">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <style>
    text {
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
    .primary { fill: $primary; }
    .secondary { fill: $secondary; }
    .serial { font-size: 10px; letter-spacing: 2.2px; }
    .name { font-size: 28px; font-weight: 700; letter-spacing: 1.2px; }
    .tagline { font-size: 11px; letter-spacing: 3.2px; }
    .node-label { font-size: 10px; font-weight: 700; letter-spacing: 1px; }
    .meta { font-size: 9px; letter-spacing: 1.2px; }
    .wire { fill: none; stroke: $line; stroke-width: 1.5; }
    .node { fill: $node_fill; stroke: $node_border; stroke-width: 1.2; }
    .cup { fill: none; stroke: $signal; stroke-width: 2; }
    .steam { fill: none; stroke: $signal; stroke-width: 1.8; stroke-linecap: round; opacity: 0.85; }
    .steam-left { animation: steam-left 4s ease-in-out infinite; }
    .steam-right { animation: steam-right 4s ease-in-out 0.8s infinite; }
    .signal { fill: $signal; filter: url(#glow); transform: translate(450px, 176px); animation: signal-route 8s ease-in-out infinite; }
    .status-dot { fill: $signal; animation: status-glow 2.4s ease-in-out infinite; }
    @keyframes steam-left {
      0%, 100% { transform: translateY(2px); opacity: 0.35; }
      50% { transform: translateY(-7px); opacity: 0.9; }
    }
    @keyframes steam-right {
      0%, 100% { transform: translateY(1px); opacity: 0.3; }
      50% { transform: translateY(-9px); opacity: 0.85; }
    }
    @keyframes signal-route {
      0%, 5% { transform: translate(450px, 176px); opacity: 0.9; }
      20% { transform: translate(145px, 176px); opacity: 1; }
      36% { transform: translate(295px, 238px); opacity: 1; }
      50% { transform: translate(450px, 176px); opacity: 0.9; }
      68% { transform: translate(605px, 238px); opacity: 1; }
      84% { transform: translate(755px, 176px); opacity: 1; }
      100% { transform: translate(450px, 176px); opacity: 0.9; }
    }
    @keyframes status-glow {
      0%, 100% { opacity: 0.55; }
      50% { opacity: 1; }
    }
    @media (prefers-reduced-motion: reduce) {
      .motion {
        animation: none !important;
      }
    }
  </style>

  <rect width="900" height="300" rx="12" fill="$background"/>
  <rect width="900" height="300" rx="12" fill="url(#grid)"/>

  <text x="30" y="31" class="secondary serial">SIGNAL LAB / BUILD 2026.07</text>
  <text x="450" y="75" text-anchor="middle" class="primary name">CHIA ZHI FENG / 谢梓峰</text>
  <text x="450" y="105" text-anchor="middle" class="secondary tagline">CODE · CIRCUITS · COFFEE</text>

  <path class="wire" d="M 430 176 L 190 176"/>
  <path class="wire" d="M 438 192 L 340 226"/>
  <path class="wire" d="M 462 192 L 560 226"/>
  <path class="wire" d="M 470 176 L 710 176"/>

  <g aria-label="Coffee input">
    <path class="steam motion steam-left" d="M 441 151 C 434 141, 448 136, 440 124"/>
    <path class="steam motion steam-right" d="M 457 151 C 450 140, 464 135, 456 122"/>
    <path class="cup" d="M 431 161 H 469 V 182 C 469 192, 461 199, 450 199 C 439 199, 431 192, 431 182 Z"/>
    <path class="cup" d="M 469 166 H 477 C 486 166, 486 181, 477 181 H 469"/>
    <path class="cup" d="M 427 203 H 476"/>
  </g>

  <g transform="translate(100 158)">
    <rect class="node" width="90" height="36" rx="6"/>
    <text x="45" y="22" text-anchor="middle" class="primary node-label">AI / ML</text>
  </g>
  <g transform="translate(250 220)">
    <rect class="node" width="90" height="36" rx="6"/>
    <text x="45" y="22" text-anchor="middle" class="primary node-label">BACKEND</text>
  </g>
  <g transform="translate(560 220)">
    <rect class="node" width="90" height="36" rx="6"/>
    <text x="45" y="22" text-anchor="middle" class="primary node-label">ROBOTS</text>
  </g>
  <g transform="translate(710 158)">
    <rect class="node" width="90" height="36" rx="6"/>
    <text x="45" y="22" text-anchor="middle" class="primary node-label">FPGA</text>
  </g>

  <circle class="signal motion" cx="0" cy="0" r="6"/>

  <text x="30" y="278" class="secondary meta">01°17′N / 103°51′E</text>
  <g transform="translate(742 272)">
    <circle class="status-dot motion" cx="0" cy="2" r="4"/>
    <text x="14" y="6" class="secondary meta">SIGNAL ONLINE</text>
  </g>
</svg>
""")


def render_svg(theme: str) -> str:
    return SVG_TEMPLATE.substitute(PALETTES[theme])


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for theme in PALETTES:
        target = ASSET_DIR / f"signal-lab-{theme}.svg"
        with target.open("w", encoding="utf-8", newline="\n") as asset:
            asset.write(render_svg(theme))


if __name__ == "__main__":
    main()
```

Run:

```powershell
python scripts/generate_signal_assets.py
```

Expected: `assets/signal-lab-dark.svg` and `assets/signal-lab-light.svg` are created with identical geometry and their specified theme palettes. The non-animated base state shows both steam paths, the signal dot over the cup, and the online indicator at full opacity.

- [ ] **Step 4: Replace the README with the approved native composition**

Replace `README.md` with this complete content:

````markdown
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/signal-lab-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/signal-lab-light.svg">
  <img alt="Animated systems schematic for Chia Zhi Feng" src="./assets/signal-lab-light.svg" width="100%">
</picture>

<p align="center">
  I study Computer Science and Design at SUTD. I like building things that connect software to the physical world.
</p>

<p align="center">
  <a href="https://zhifeng-portfolio.vercel.app/">Portfolio</a>
  &nbsp;·&nbsp;
  <a href="https://www.linkedin.com/in/zhi-feng-chia-a50266210/">LinkedIn</a>
  &nbsp;·&nbsp;
  <a href="mailto:zhifeng010729@gmail.com">Email</a>
</p>

<details>
<summary><code>brew --profile</code></summary>
<br>

```text
coffee      kopi o kosong
location    singapore
currently   studying at SUTD and tinkering
serious     zhifeng-portfolio.vercel.app
```

</details>

<details>
<summary><code>why the username?</code></summary>
<br>

Kopi o kosong beng is simply my coffee order: black coffee, no sugar, iced.

</details>
````

- [ ] **Step 5: Run the complete profile contract test**

Run:

```powershell
python -m unittest -v tests/test_profile.py
```

Expected: five tests pass with no failures or errors.

- [ ] **Step 6: Run structural checks**

Run:

```powershell
git diff --check
python -c "import xml.etree.ElementTree as ET; ET.parse('assets/signal-lab-dark.svg'); ET.parse('assets/signal-lab-light.svg'); print('SVG XML valid')"
```

Expected: `git diff --check` prints nothing and the XML command prints `SVG XML valid`.

- [ ] **Step 7: Render and inspect both themes**

Use Playwright to render a temporary local HTML page containing the exact README `<picture>`, identity line, links, and open and closed `<details>` states.

Capture these four views:

```text
desktop dark:  1200 × 900, dark colour scheme
desktop light: 1200 × 900, light colour scheme
mobile dark:    390 × 844, dark colour scheme
mobile light:   390 × 844, light colour scheme
```

Inspect each image for clipped name text, overlapping nodes, low contrast, broken theme selection, unreadable mobile labels, and an excessive website-like appearance. Any defect found must be fixed and covered by the profile contract where practical.

- [ ] **Step 8: Commit the implementation**

Run:

```powershell
git add -- README.md scripts/generate_signal_assets.py assets/signal-lab-dark.svg assets/signal-lab-light.svg tests/test_profile.py
git commit -m "feat: build animated signal lab profile"
```

The commit must have Zhi Feng as its sole author and no co-author trailers.

---

### Task 2: Audience review and evidence-based refinement

**Files:**
- Modify if required: `README.md`
- Modify if required: `assets/signal-lab-dark.svg`
- Modify if required: `assets/signal-lab-light.svg`
- Modify if required: `scripts/generate_signal_assets.py`
- Modify if required: `tests/test_profile.py`

**Interfaces:**
- Consumes: the rendered desktop and mobile views from Task 1
- Produces: a reviewed profile that preserves the approved creative role while addressing concrete audience problems

- [ ] **Step 1: Request three independent audience reviews**

Give each reviewer the rendered images, README text, design spec, and these role-specific questions:

```text
HR manager: Is the profile memorable, readable, and safe to encounter during a professional background check without turning into a résumé?

pitchMe employee: Does the profile feel like Zhi Feng's personal creative project without making pitchMe look secondary, abandoned, or used as a job-search prop?

ordinary GitHub visitor: Can you understand the profile within ten seconds, do the effects feel interesting rather than broken, and would you click any of the three links or Easter eggs?
```

Each reviewer must report strengths, points of confusion, concrete changes, and a verdict of `approve` or `revise`.

- [ ] **Step 2: Triage the feedback**

Accept feedback that identifies a concrete readability, tone, rendering, accessibility, or audience problem. Reject preference-only changes that would restore portfolio duplication, job-seeking copy, startup promotion, marketing language, or generic GitHub statistics.

Record every accepted item and its source role before editing.

- [ ] **Step 3: Add a failing regression assertion for each accepted functional or copy issue**

Add the smallest assertion that proves the issue to `tests/test_profile.py`, then run:

```powershell
python -m unittest -v tests/test_profile.py
```

Expected: the new assertion fails for the issue identified by the reviewer.

Pure visual refinements that cannot be expressed as stable structural assertions are verified through the same four rendered views instead.

- [ ] **Step 4: Implement the accepted refinements**

Change only the files needed to address accepted findings. Preserve all Global Constraints and the four-part README composition.

- [ ] **Step 5: Verify the refinements**

Run:

```powershell
python -m unittest -v tests/test_profile.py
git diff --check
```

Expected: all tests pass and `git diff --check` prints nothing. Re-render any theme or viewport affected by the changes and inspect it again.

- [ ] **Step 6: Commit the review refinements if any files changed**

Run:

```powershell
git add -- README.md scripts/generate_signal_assets.py assets/signal-lab-dark.svg assets/signal-lab-light.svg tests/test_profile.py
git commit -m "fix: refine profile after audience review"
```

If no changes are justified, do not create an empty commit. Any commit must have Zhi Feng as its sole author and no co-author trailers.
