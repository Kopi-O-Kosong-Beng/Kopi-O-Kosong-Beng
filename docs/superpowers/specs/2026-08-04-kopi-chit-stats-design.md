# The Tab: live GitHub stats as a hawker order chit

Date: 2026-08-04
Status: approved, ready for implementation

## Problem

The profile has no activity signal. The obvious fix is a third party stats widget,
which the existing guard suite bans on purpose: `github-readme-stats`,
`streak-stats`, `github-profile-trophy`, `contribution-graph` and `shields.io` are
all forbidden strings in `tests/test_profile.py`. Those widgets carry their own
fonts, palettes and framing, so any of them would sit on the page looking borrowed.

The profile also currently contains zero numbers in prose, enforced by a test that
allows only the digits `18`.

## Solution

Generate a second SVG asset in the same visual language as the signboard, fed by
real contribution data. No third party service is contacted at render time and no
banned string is introduced, so the guard suite stays intact and unweakened.

The numbers live inside the SVG artwork. The `prose_only` helper in
`tests/test_profile.py` already strips HTML attribute values before scanning for
digits, so the READMEs stay number free with no change to that rule.

## Visual design

One card, `900 x 360`, sitting directly beneath the signboard so the two read as a
single stall front.

Left, `x 44..592`: a thermal printed order chit with a torn bottom edge.

```
KOPI O KOSONG BENG
ORDER #0412  ·  04 AUG 2026
..........................................
1x   commits, past year               412
1x   longest run                   7 days
1x   days brewed                   49/366
..........................................
LAST 30 DAYS
[ 30 bar sparkline ]
..........................................
TOTAL                             no sugar
\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/
```

Right, `x 620..880`: a tall glass of iced kopi, drawn larger than the one on the
sign so it reads as the hero of this card.

- Coffee level is `days_active / days_total`, the share of the past year with at
  least one contribution. The glass literally fills as he shows up.
- Ice cubes are his stack, one cube per entry, sized by rank, each stamped with a
  short label. Captioned `TODAY'S BREW`, echoing the strip on the signboard.
- Straw, condensation drops and the `bead` keyframes are carried over from the
  signboard unchanged.

Palette tokens come from `generate_kopi_sign.PALETTES` with no additions, so light
and dark stay in lockstep with the sign.

### Motion

Two animations, both authored so the still state is the correct final state.

- `.motion` drops reuse the existing `bead` keyframes.
- `.pour` raises the coffee from below to its level on load. With animation
  disabled the coffee already sits at its final level.

The reduced motion block handles both, and keeps the existing `.motion` opacity
behaviour so the drops fade rather than freeze mid fall:

```css
@media (prefers-reduced-motion: reduce) {
  .motion { animation: none !important; opacity: 0.7 !important; }
  .pour   { animation: none !important; }
}
```

## Data source

`https://github.com/users/<login>/contributions`, fetched with no authentication.

Verified on 2026-08-04: returns HTTP 200 and 366 day cells, each carrying
`data-date`, `data-level` and an `id`, with exact per day counts in a matching
`<tool-tip>` element keyed by `for`. This is the same calendar the public profile
page renders, so private contributions are included the moment the account enables
Settings, Profile, "Include private contributions on my profile".

That checkbox is the entire setup. It is account level and permanent: every private
repo, including ones created later, counts automatically from the day it exists.
No token, no repo secret, nothing that expires.

### Two traps this endpoint sets

**DOM order is not chronological.** Cell ids run `component-<weekday>-<week>`, so the
markup lists every Sunday, then every Monday, and so on. The first three cells in
the response were `2025-08-03`, `2025-08-10`, `2025-08-17`. Parsing must sort by
`data-date` and must never trust document order.

**Counts live in sibling elements.** The `<td>` carries only a coarse `data-level`
bucket from 0 to 4. Exact counts are in `<tool-tip for="...">` text such as
`3 contributions on August 5th.` or `No contributions on August 3rd.`, joined to
the cell by id.

Parsing uses `html.parser.HTMLParser` from the standard library rather than regular
expressions, because attribute order is not guaranteed. The repo has no third party
dependencies and this does not add one.

### Why languages are curated, not fetched

The account has 3 public repos, one a fork, and the API reports their languages as
`Python`, `Python` and `null`. Auto detection would render a single lonely `python`
ice cube. Real work lives in private repos, and reading language bytes out of those
is the one thing that would have required a `repo` scoped token.

So the stack stays curated, exactly as the signboard already curates it. `STACK` is
lifted out of `generate_kopi_sign.py` as a module constant and both cards read from
it, making it a single source of truth instead of two hardcoded lists that drift.

## Architecture

Network and drawing are kept strictly apart so the drawing stays testable.

| Unit | Responsibility | Depends on |
| --- | --- | --- |
| `scripts/fetch_kopi_stats.py` | One HTTP fetch, parse, write `data/stats.json` | network |
| `scripts/generate_kopi_chit.py` | Pure: stats dict to SVG string | palettes, stack |
| `.github/workflows/brew.yml` | Daily fetch, generate, test, commit if changed | both |

`data/stats.json` is committed. That is what preserves the existing byte exact drift
test under changing data: the asset must equal `render_chit(theme, <committed json>)`.
Live data never enters a test.

### `data/stats.json`

```json
{
  "login": "Kopi-O-Kosong-Beng",
  "generated_on": "2026-08-04",
  "window_start": "2025-08-03",
  "window_end": "2026-08-03",
  "total_contributions": 412,
  "days_active": 49,
  "days_total": 366,
  "longest_run": 7,
  "current_run": 2,
  "recent": [0, 1, 3, 0, "... 30 entries, oldest first"]
}
```

### Failure behaviour

The scrape is the one fragile piece. `fetch_kopi_stats.py` refuses to write unless
it parses at least 300 day cells with counts. On failure the workflow leaves the
previous `data/stats.json` in place, so the card goes stale rather than breaking or
rendering zeros.

## Testing

`tests/test_chit.py`, mirroring the signboard contract:

1. Both assets exist, are pure ASCII, start with the XML declaration, LF only.
2. Assets match `render_chit(theme, committed_stats)` byte for byte.
3. Geometry and accessibility: `viewBox`, `role="img"`, `aria-labelledby`, `<title>`,
   `<desc>`, reduced motion block, and no `<script>`, `<image>`, `@font-face`,
   `xlink:href`, `href="`, `https://` or protocol relative `//`.
4. Light and dark differ only by palette token substitution.
5. Copy contract: chit headings and every stack label present.
6. Purity and edge cases, driven by fixtures rather than live data:
   - all zero series produces no divide by zero and a flat baseline
   - fully active series yields fill `1.0` and a run equal to the series length
   - longest run is correct across a known series with gaps
   - stack labels containing `&` or `<` are XML escaped and the result still parses
   - thousands separators appear on large counts
7. `data/stats.json` schema: required keys present, `recent` has 30 entries,
   `days_active <= days_total`.
8. Both cards derive their stack from `generate_kopi_sign.STACK`.

`tests/test_profile.py` gains guards that both READMEs carry the chit in a
`<picture>` with both themes, that its `<img>` has real alt text, and that the chit
is always a local `./assets/` path and never a remote URL. Every existing check is
kept as is.

## Non goals

- No stars or repo counts. Both are near zero and would read as thin.
- No streak service, no trophy wall, no badges. The guard list stands.
- No public numbers in README prose. The digits stay inside the artwork.

## Known tension

The profile was built with deliberately zero metrics. A chit is far closer to
personality than to a trophy wall, but it is still a move from "no numbers" to
"some numbers", and that was accepted knowingly.

Separately, the calendar currently shows 49 active days out of 366. For someone
shipping a product full time that is under counting, and the two usual causes are
the private contributions checkbox being off, or pitchMe commits carrying a git
email that is not attached to this GitHub account. Worth confirming before these
numbers go on a public card.
