from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_kopi_stats  # noqa: E402

STATS_FILE = ROOT / "data" / "stats.json"


def cell(weekday, week, date, level):
    return (
        f'<td data-date="{date}" id="contribution-day-component-{weekday}-{week}" '
        f'data-level="{level}" role="gridcell" class="ContributionCalendar-day"></td>'
    )


def tip(weekday, week, text):
    return (
        f'<tool-tip for="contribution-day-component-{weekday}-{week}" '
        f'data-view-component="true" class="sr-only">{text}</tool-tip>'
    )


class CalendarParsingTests(unittest.TestCase):
    def test_days_come_back_in_date_order_not_document_order(self):
        """GitHub emits every Sunday, then every Monday, and so on.

        The first three cells of a real response were 2025-08-03, 2025-08-10
        and 2025-08-17: three consecutive Sundays, seven days apart. Trusting
        document order would scramble every streak and every sparkline, so the
        parser has to sort on data-date.
        """
        markup = "".join(
            [
                cell(0, 0, "2026-01-04", 0),
                cell(0, 1, "2026-01-11", 1),
                cell(1, 0, "2026-01-05", 2),
                cell(1, 1, "2026-01-12", 0),
                tip(0, 0, "No contributions on January 4th."),
                tip(0, 1, "1 contribution on January 11th."),
                tip(1, 0, "2 contributions on January 5th."),
                tip(1, 1, "No contributions on January 12th."),
            ]
        )
        days = fetch_kopi_stats.parse_calendar(markup)
        self.assertEqual(
            days,
            [
                ("2026-01-04", 0),
                ("2026-01-05", 2),
                ("2026-01-11", 1),
                ("2026-01-12", 0),
            ],
        )

    def test_exact_counts_are_read_from_the_tooltip_not_the_level(self):
        """data-level is a bucket from 0 to 4. The real number is in the tip."""
        markup = cell(0, 0, "2026-01-04", 4) + tip(
            0, 0, "37 contributions on January 4th."
        )
        self.assertEqual(fetch_kopi_stats.parse_calendar(markup), [("2026-01-04", 37)])

    def test_the_singular_and_the_empty_phrasings_both_parse(self):
        for text, expected in (
            ("No contributions on March 2nd.", 0),
            ("1 contribution on March 2nd.", 1),
            ("12 contributions on March 2nd.", 12),
            ("1,024 contributions on March 2nd.", 1024),
        ):
            with self.subTest(text=text):
                markup = cell(0, 0, "2026-03-02", 1) + tip(0, 0, text)
                self.assertEqual(
                    fetch_kopi_stats.parse_calendar(markup), [("2026-03-02", expected)]
                )

    def test_a_cell_with_no_matching_tooltip_is_dropped(self):
        markup = (
            cell(0, 0, "2026-01-04", 0)
            + cell(0, 1, "2026-01-11", 1)
            + tip(0, 1, "1 contribution on January 11th.")
        )
        self.assertEqual(fetch_kopi_stats.parse_calendar(markup), [("2026-01-11", 1)])


class SummaryTests(unittest.TestCase):
    @staticmethod
    def series(counts, start="2026-01-01"):
        from datetime import date, timedelta

        first = date.fromisoformat(start)
        return [
            ((first + timedelta(days=i)).isoformat(), c) for i, c in enumerate(counts)
        ]

    def test_longest_run_spans_the_biggest_unbroken_block(self):
        days = self.series([1, 1, 0, 1, 1, 1, 1, 0, 1])
        summary = fetch_kopi_stats.summarise(days, today="2026-01-09")
        self.assertEqual(summary["longest_run"], 4)

    def test_current_run_counts_back_from_today_and_stops_at_a_gap(self):
        days = self.series([1, 1, 1, 0, 1, 1])
        summary = fetch_kopi_stats.summarise(days, today="2026-01-06")
        self.assertEqual(summary["current_run"], 2)

    def test_a_silent_year_summarises_without_dividing_by_zero(self):
        days = self.series([0] * 40)
        summary = fetch_kopi_stats.summarise(days, today="2026-02-09")
        self.assertEqual(summary["total_contributions"], 0)
        self.assertEqual(summary["days_active"], 0)
        self.assertEqual(summary["longest_run"], 0)
        self.assertEqual(summary["current_run"], 0)
        self.assertEqual(summary["days_total"], 40)

    def test_days_after_today_never_count(self):
        """The calendar pads the final week with dates that have not happened."""
        days = self.series([1, 1, 0, 0])
        summary = fetch_kopi_stats.summarise(days, today="2026-01-02")
        self.assertEqual(summary["days_total"], 2)
        self.assertEqual(summary["days_active"], 2)
        self.assertEqual(summary["current_run"], 2)
        self.assertEqual(summary["window_end"], "2026-01-02")

    def test_recent_holds_thirty_days_oldest_first(self):
        days = self.series(list(range(40)))
        summary = fetch_kopi_stats.summarise(days, today="2026-02-09")
        self.assertEqual(len(summary["recent"]), 30)
        self.assertEqual(summary["recent"], list(range(10, 40)))

    def test_recent_is_padded_when_the_history_is_short(self):
        days = self.series([2, 3])
        summary = fetch_kopi_stats.summarise(days, today="2026-01-02")
        self.assertEqual(len(summary["recent"]), 30)
        self.assertEqual(summary["recent"][-2:], [2, 3])
        self.assertEqual(summary["recent"][:-2], [0] * 28)


class GuardTests(unittest.TestCase):
    def test_a_short_parse_is_rejected_rather_than_written(self):
        """A markup change upstream should leave the last good file alone."""
        with self.assertRaises(fetch_kopi_stats.CalendarError):
            fetch_kopi_stats.validate([("2026-01-01", 1)] * 299)

    def test_a_full_year_passes_the_guard(self):
        fetch_kopi_stats.validate([("2026-01-01", 1)] * 366)


class CommittedStatsTests(unittest.TestCase):
    def test_the_committed_stats_file_matches_the_schema_the_chit_expects(self):
        stats = json.loads(STATS_FILE.read_text(encoding="utf-8"))
        for key in (
            "login",
            "generated_on",
            "window_start",
            "window_end",
            "total_contributions",
            "days_active",
            "days_total",
            "longest_run",
            "current_run",
            "recent",
        ):
            self.assertIn(key, stats)
        self.assertEqual(len(stats["recent"]), 30)
        self.assertLessEqual(stats["days_active"], stats["days_total"])
        self.assertLessEqual(stats["longest_run"], stats["days_total"])
        self.assertLessEqual(stats["current_run"], stats["longest_run"])
        self.assertGreater(stats["days_total"], 300)

    def test_the_stats_file_is_lf_only_so_the_asset_stays_reproducible(self):
        self.assertNotIn(b"\r\n", STATS_FILE.read_bytes())


if __name__ == "__main__":
    unittest.main()
