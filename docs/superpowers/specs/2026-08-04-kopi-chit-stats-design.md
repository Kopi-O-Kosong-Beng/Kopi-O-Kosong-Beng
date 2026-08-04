# The Counter: a second card, and why it stopped being a stats card

Date: 2026-08-04
Status: shipped

## What it is now

A second generated asset, `kopi-chit-{light,dark}.svg`, sitting under the
signboard. It lists what is being built and what each thing is built with, plus
one live line at the foot saying when the account last pushed.

The project list is curated in `COUNTER` in `scripts/generate_kopi_chit.py`,
exactly as `STACK` is curated for the signboard. Editing that tuple changes the
card; the daily workflow redraws it.

## How it got here

The brief was "add GitHub stats". Six designs were built and thrown away before
the premise itself turned out to be the problem. Recording them so none of them
comes back.

| Design | Why it went |
| --- | --- |
| Chit beside a second glass | The signboard already draws a glass and already prints the stack, so it repeated the picture and the words at once |
| A calendar of small squares | That is GitHub's own graphic, on the same page, in a warmer palette |
| Twelve monthly cup rings | Nine of the twelve months are empty, so any per month layout is a row of holes |
| Seven glasses, one per weekday | Small multiples turn a card into a dashboard, and most of each glass was empty outline |
| A weekday split strip | Tells a stranger which day he does not work |
| A scored activity headline | See below |

### The window was lying

Every unflattering number came from measuring 366 days.

| Window | Reads as |
| --- | --- |
| 366 days | 45 active days, 12 per cent, a dormant account |
| 30 days | 27 active days, 90 per cent, someone shipping most days |

Both true. 666 of the 726 commits landed in the final month, because the account
was genuinely quiet before that. **When a figure looks bad, check the
measurement period before changing the metric.**

### Then the metrics went too

Reframing fixed the honesty but not the point. Activity numbers are the weakest
signal on a profile: gameable, and about typing rather than judgement. Worse,
several were actively harmful to the person they describe.

- "57 per cent of the year in its 10 busiest days" reads as inconsistent.
- "45 of 366 active days" reads as an abandoned account.
- A quietest weekday tagged `closed` reads as "does not work Fridays".

The repo's own guard suite had banned stats widgets before any of this was
built. That decision was right, and it was right for this reason.

## What a visitor actually wants

They want to know what this person builds and what they build it with. The
README says the first in prose and never says the second at all, which is the
gap the card now fills. Nothing on it decays when a habit changes, and there is
no number that can undersell anyone.

The single exception is the footer. Proof that an account is not abandoned is
the one thing activity data can usefully tell a visitor, and it costs one line:
`LAST SERVED / TODAY`.

## Data source

`https://github.com/users/<login>/contributions`, fetched with no
authentication. Verified 2026-08-04: HTTP 200, 366 day cells with exact per day
counts. It is the calendar the public profile renders, so private contributions
are included once the account enables Settings, Profile, "Include private
contributions on my profile". That checkbox is the entire setup, it is account
level and permanent, and no token or repo secret is involved.

Only the footer needs this now, but the pipeline is kept: it is what makes the
card able to say anything live at all.

### Two traps this endpoint sets

**DOM order is not chronological.** Cell ids run `component-<weekday>-<week>`, so
the markup lists every Sunday, then every Monday. Parsing must sort on
`data-date`.

**Counts live in sibling elements.** The `<td>` carries only a coarse
`data-level` bucket. Exact counts are in `<tool-tip for="...">` text, joined by
id. Parsing uses `html.parser` rather than regular expressions, because
attribute order is not guaranteed.

## Architecture

| Unit | Responsibility | Depends on |
| --- | --- | --- |
| `scripts/fetch_kopi_stats.py` | One HTTP fetch, parse, write `data/stats.json` | network |
| `scripts/generate_kopi_chit.py` | Pure: `COUNTER` plus stats dict to SVG | palettes |
| `.github/workflows/brew.yml` | Daily fetch, generate, test, commit if changed | both |

`data/stats.json` is committed, which is what preserves the byte exact drift
test under changing data: the asset must equal the generator run over the
committed file. Live data never enters a test.

`fetch_kopi_stats.py` refuses to write unless it parses at least 300 day cells,
so a markup change upstream leaves the previous file in place and the card goes
stale rather than wrong.

## Guards worth keeping

- **No scoreboard.** Tests fail if a commit total, a streak, a year ratio or a
  percentage reaches any drawn `<text>` element. This is the lesson above, held
  in place mechanically.
- **Nothing animated hides itself at rest.** No animation may declare a `both`
  or `backwards` fill-mode, and every animated element must carry a class the
  reduced motion block switches off. An early version poured coffee up into a
  glass and rendered an empty glass anywhere the animation was not running,
  because a renderer parked at `t=0` sits on the `from` frame regardless of
  fill-mode.
- **The two cards may not disagree.** Every stack tag on the counter must be one
  the signboard also claims.
- **Layout is asserted, not eyeballed.** Row separators must not cross the stack
  chips, and no chip row may run past the right margin. Both were real bugs.
- **Paper grain is generated.** `feTurbulence`, not a bitmap, because GitHub's
  image proxy would leave a fetched texture blank.

## Still open

The account shows 45 active days out of 366 because private contributions are
not being counted. Either the profile checkbox is off, or pitchMe commits carry
a git email not attached to this GitHub account.
