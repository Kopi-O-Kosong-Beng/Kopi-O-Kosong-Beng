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

One card, `900 x 410`, sitting directly beneath the signboard so the two read as a
single stall front: a full width thermal printed order chit with a torn bottom
edge.

**There is deliberately no second glass.** The first build put a tall glass of
iced kopi beside the chit, filling to the share of days brewed with the stack
stamped on its ice cubes. Stacked under the signboard it read as two cups on one
profile, and worse, it repeated the stack twice: once as pictures on the ice and
once as words along the signboard's specials strip. The glass stays on the sign,
where it belongs, and the chit became the receipt it always was.

**And there is deliberately no contribution grid.** The freed space first went to
a calendar of small squares, one per day. That is the graphic GitHub already
draws on the same page, and repainting it in a warmer palette is precisely the
borrowed look the guard suite exists to keep off this profile. Designing a stats
card is not the same as reskinning one.

**Nor twelve monthly cup rings**, which were tried next. The problem was the
data, not the drawing: nine of the twelve months in this account are empty, so
any per month layout is a row of holes however carefully it is rendered.

The card shows **the last thirty days**, full width, one bar per day. That is the
only window where this data is dense, 28 of 30 days active, and it visibly moves
every morning. Height scales linearly, which is the honest encoding for a bar,
where length does the reading. The axis names the date of the leftmost bar so it
is not a mystery ruler.

### The copy says what it measures

The first pass leaned on the receipt metaphor and the puns did not map onto the
numbers underneath. `days brewed` was not a thing anyone buys, `SERVED SINCE`
read like the stall opened that day rather than naming a rolling window, and a
`TOTAL` row whose value was "no sugar" totalled nothing while repeating the
sign-off sitting directly beneath it in the README.

The labels are now plain: `commits, past year`, `longest streak`, `days active`,
and a footer that states the window the card is counting over. The kopi theme
lives in the paper, the ink, the torn edge and the signboard above it, which is
enough. It does not need every label to be a joke.

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

Every animation starts and ends at the resting state, and none of them moves
the coffee.

- `.motion` drops reuse the existing `bead` keyframes.
- `.bob` floats each ice cube, staggered, on an outer group. The tilt stays on
  an inner group, because a CSS transform on the same element replaces the
  `transform` attribute outright and would flatten every cube.
- `.brew-top` ripples the crema horizontally around its own centre.

The first attempt poured the coffee up into the glass from below. It looked
right in a live browser and rendered an **empty glass** anywhere the animation
was not actually running, because a renderer parked at t=0 sits on the `from`
frame whether or not a fill-mode is set. Dropping the fill-mode is not enough.
The level is now plain geometry and only decoration moves.

```css
@media (prefers-reduced-motion: reduce) {
  .motion { animation: none !important; opacity: 0.7 !important; }
  .still  { animation: none !important; }
}
```

`tests/test_chit.py` locks this in: no animation may declare a `both` or
`backwards` fill-mode, and every animated element must carry a class the
reduced motion block switches off.

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
