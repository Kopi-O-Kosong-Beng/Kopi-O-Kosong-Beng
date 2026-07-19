# GitHub Profile Animated Signal Lab Design

Date: 2026-07-19

## Purpose

The GitHub profile is Zhi Feng's experimental technical signature. It should be memorable and fun to build without duplicating the professional material already available on the portfolio website and LinkedIn.

The README should feel native to GitHub. It should not resemble a landing page, résumé, or project case study. The profile repository is a small creative project in its own right.

## Positioning

The profile presents Zhi Feng as someone who enjoys working across software and the physical world. It hints at AI and machine learning, backend systems, robotics, and FPGA hardware without describing individual projects or advertising for work.

pitchMe is not featured in the main composition. Visitors who want professional evidence can follow the portfolio or LinkedIn links.

## Experience goals

1. The animated graphic should create an immediate visual signature.
2. The README should remain recognisably GitHub Markdown.
3. The writing should sound casual and human, not like marketing copy.
4. The profile should reward curiosity through small native GitHub interactions.
5. The design must work in both light and dark GitHub themes.
6. A static rendering must remain complete if animation is unavailable.

## README composition

The finished README contains only four elements, in this order:

1. A theme-aware animated Signal Lab SVG.
2. One short identity line: `I study Computer Science and Design at SUTD. I like building things that connect software to the physical world.`
3. Centred links to the portfolio, LinkedIn, and email.
4. Two native `<details>` Easter eggs.

There are no project tables, skill icon walls, GitHub statistics cards, contribution graphs, job-seeking statements, startup metrics, or long biography sections.

## Animated Signal Lab artwork

### Content

The SVG displays:

- `CHIA ZHI FENG / 谢梓峰`
- `CODE · CIRCUITS · COFFEE`
- the serial label `SIGNAL LAB / BUILD 2026.07`
- a central kopi cup with animated steam
- four connected nodes labelled `AI / ML`, `BACKEND`, `ROBOTS`, and `FPGA`
- a glowing signal that travels from the cup through the technical nodes
- Singapore coordinates `01°17′N / 103°51′E`
- a small `SIGNAL ONLINE` indicator

The visual language is a restrained engineering schematic. Fine grid lines, node boxes, and signal paths provide the blueprint character. Kopi is the personal motif, not a separate brand or mascot.

### Theme variants

Two assets are stored in `assets/`:

- `signal-lab-dark.svg`
- `signal-lab-light.svg`

The README selects the correct asset with a `<picture>` element and `prefers-color-scheme` media sources. Both assets use the same layout and animation timing. Only colour tokens change.

The dark palette uses deep navy, muted cyan grid lines, off-white type, and teal signals. The light palette uses warm off-white, slate lines, dark navy type, and a darker teal signal for sufficient contrast.

### Motion

Motion is deliberately limited to:

- two soft steam strokes rising above the kopi cup
- one signal pulse travelling through the network
- a subtle glow on the online indicator

The animation loops slowly and avoids flashing. SVG CSS includes a `prefers-reduced-motion: reduce` rule that stops all movement while preserving the complete static artwork.

If GitHub's image proxy does not play the animation, the first frame must still read as a finished schematic.

### Responsive behaviour

Each SVG uses `viewBox="0 0 900 300"` and scales to the README width. Important text and nodes remain within a mobile-safe central area. Coordinates and serial markings remain visible at narrow widths with lower contrast than the name and nodes, and no elements overlap.

## Native GitHub interactions

The README uses two collapsed `<details>` blocks.

The first is labelled `brew --profile` and contains:

```text
coffee      kopi o kosong
location    singapore
currently   studying at SUTD and tinkering
serious     portfolio link
```

The second is labelled `why the username?` and explains the coffee order in one or two natural sentences.

These are the only interactive elements. GitHub README files cannot run JavaScript, so the design does not imply unsupported hover, click, or navigation behaviour.

## Links

- Portfolio: `https://zhifeng-portfolio.vercel.app/`
- LinkedIn: `https://www.linkedin.com/in/zhi-feng-chia-a50266210/`
- Email: `mailto:zhifeng010729@gmail.com`

Links use plain inline Markdown separated by centred dots. They do not use shields, button styling, or a navigation-bar treatment.

## Accessibility and fallback

- The `<img>` has concise alt text describing the animated systems schematic.
- Text in the artwork meets practical contrast requirements in both themes.
- No essential information is conveyed only through colour or motion.
- Reduced motion is honoured inside each SVG.
- The README remains understandable when images are disabled.
- External third-party rendering services are not required for the main experience.

## Repository layout

```text
README.md
assets/
  signal-lab-dark.svg
  signal-lab-light.svg
scripts/
  generate_signal_assets.py
tests/
  test_profile.py
docs/
  superpowers/
    specs/
      2026-07-19-github-profile-signal-lab-design.md
```

The local `.superpowers/` brainstorming directory is ignored and never committed.
The generator keeps both theme variants on identical geometry. The test file records the README and SVG contract so later edits cannot silently restore the old marketing copy or break the theme variants.

## Verification

Implementation is complete only after all of the following pass:

1. Both SVG files parse as valid XML.
2. Both theme variants render without clipping at desktop and narrow widths.
3. Reduced motion produces a complete static composition.
4. README links resolve to the intended destinations.
5. Markdown and HTML nesting are valid for GitHub's renderer.
6. `git diff --check` reports no whitespace errors.
7. The final Git diff contains only the agreed profile files.

## Out of scope

- Rewriting the portfolio website or LinkedIn profile
- Adding project case studies to GitHub
- Publishing job availability or internship dates
- GitHub statistics, trophy, language, or streak cards
- Contribution snakes or 3D contribution graphs
- Scheduled workflows or third-party profile services
- Changes to repository visibility, pinned repositories, or GitHub account settings
