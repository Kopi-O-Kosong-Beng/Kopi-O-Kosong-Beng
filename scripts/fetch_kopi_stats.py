"""Read the public contribution calendar and write data/stats.json.

No authentication, no token, no repo secret. The endpoint below is the same
calendar the public profile page renders, so private contributions are counted
as soon as the account enables Settings, Profile, "Include private
contributions on my profile". That checkbox is account level and permanent, so
private repos created later are picked up with no further setup.
"""

from datetime import date
from html.parser import HTMLParser
from pathlib import Path
import json
import os
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "stats.json"

CALENDAR_URL = "https://github.com/users/{login}/contributions"
DEFAULT_LOGIN = "Kopi-O-Kosong-Beng"
USER_AGENT = "kopi-o-kosong-beng-profile-card"

# A real response carries a full year of cells. Anything much shorter means the
# markup moved under us, and a wrong card is worse than a stale one.
MIN_DAYS = 300

# "No contributions on August 3rd." / "1 contribution on ..." / "12 contributions on ..."
COUNT = re.compile(r"^([\d,]+|No)\s+contributions?\b", re.IGNORECASE)


class CalendarError(RuntimeError):
    """The response did not look like a contribution calendar."""


class _CalendarParser(HTMLParser):
    """Walk the tags rather than regexing them, because attribute order is not
    guaranteed and the exact count is not on the cell.

    The cell carries only data-level, a bucket from 0 to 4. The real number sits
    in a sibling <tool-tip> joined to the cell by its id.
    """

    def __init__(self):
        super().__init__()
        self._dates = {}
        self._counts = {}
        self._open_tip = None
        self._buffer = []

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag == "td" and "ContributionCalendar-day" in (attr.get("class") or ""):
            if attr.get("id") and attr.get("data-date"):
                self._dates[attr["id"]] = attr["data-date"]
        elif tag == "tool-tip" and attr.get("for"):
            self._open_tip = attr["for"]
            self._buffer = []

    def handle_data(self, data):
        if self._open_tip is not None:
            self._buffer.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self._open_tip is not None:
            match = COUNT.match("".join(self._buffer).strip())
            if match:
                raw = match.group(1)
                self._counts[self._open_tip] = (
                    0 if raw.lower() == "no" else int(raw.replace(",", ""))
                )
            self._open_tip = None
            self._buffer = []

    @property
    def days(self):
        # Sorting is not cosmetic. GitHub emits every Sunday, then every Monday,
        # so document order is weekday major. ISO dates sort chronologically.
        return sorted(
            (self._dates[cell], self._counts[cell])
            for cell in self._dates
            if cell in self._counts
        )


def parse_calendar(markup):
    parser = _CalendarParser()
    parser.feed(markup)
    parser.close()
    return parser.days


def validate(days):
    if len(days) < MIN_DAYS:
        raise CalendarError(
            f"Parsed {len(days)} day cells, expected at least {MIN_DAYS}. "
            "Leaving the previous stats file in place."
        )
    return days


def summarise(days, today, login=DEFAULT_LOGIN):
    cutoff = date.fromisoformat(today)
    history = [pair for pair in days if date.fromisoformat(pair[0]) <= cutoff]
    counts = [count for _, count in history]

    longest = run = 0
    for count in counts:
        run = run + 1 if count > 0 else 0
        longest = max(longest, run)

    current = 0
    for count in reversed(counts):
        if count == 0:
            break
        current += 1

    return {
        "login": login,
        "generated_on": today,
        "window_start": history[0][0] if history else today,
        "window_end": history[-1][0] if history else today,
        "total_contributions": sum(counts),
        "days_active": sum(1 for count in counts if count > 0),
        "days_total": len(history),
        "longest_run": longest,
        "current_run": current,
        # One entry per day of the window, oldest first, so the card can draw
        # the calendar grid without needing the dates again.
        "daily": counts,
    }


def fetch(login):
    request = urllib.request.Request(
        CALENDAR_URL.format(login=login),
        headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def write(summary):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main():
    login = os.environ.get("KOPI_LOGIN", DEFAULT_LOGIN)
    days = validate(parse_calendar(fetch(login)))
    write(summarise(days, today=date.today().isoformat(), login=login))


if __name__ == "__main__":
    main()
