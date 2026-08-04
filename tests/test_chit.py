from pathlib import Path
import json
import re
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_kopi_chit as chit  # noqa: E402
import generate_kopi_sign  # noqa: E402

ASSET_PATHS = {
    "dark": ROOT / "assets" / "kopi-chit-dark.svg",
    "light": ROOT / "assets" / "kopi-chit-light.svg",
}

STATS_FILE = ROOT / "data" / "stats.json"

NON_FINITE = re.compile(r"\b(nan|-?inf(inity)?)\b", re.IGNORECASE)


def stats(**overrides):
    base = {
        "login": "Kopi-O-Kosong-Beng",
        "generated_on": "2026-08-04",
        "window_start": "2025-08-03",
        "window_end": "2026-08-03",
        "total_contributions": 739,
        "days_active": 45,
        "days_total": 366,
        "longest_run": 23,
        "current_run": 5,
        "daily": [0] * 336 + [3] * 30,
    }
    base.update(overrides)
    return base


def drawn(theme):
    """Only what a reader sees. itertext() would sweep in the <style> block."""
    source = ASSET_PATHS[theme].read_text(encoding="utf-8")
    return "\n".join(re.findall(r"<text[^>]*>([^<]*)</text>", source))


class AssetContractTests(unittest.TestCase):
    def test_both_assets_exist_and_are_pure_ascii(self):
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                self.assertTrue(path.exists(), f"Missing {path}")
                source = path.read_text(encoding="utf-8")
                self.assertTrue(
                    source.startswith('<?xml version="1.0" encoding="UTF-8"?>\n')
                )
                self.assertTrue(source.isascii(), "SVG must be ASCII only")
                self.assertNotIn(b"\r\n", path.read_bytes())

    def test_assets_match_the_generator_run_over_the_committed_stats(self):
        """The drift test survives changing data because the input is committed.

        Live numbers never reach a test. The asset must equal the generator run
        over data/stats.json, so a stale asset and a hand edited asset both fail.
        """
        committed = json.loads(STATS_FILE.read_text(encoding="utf-8"))
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                self.assertEqual(
                    path.read_text(encoding="utf-8"),
                    chit.render_chit(theme, committed),
                    "Asset has drifted. Re-run scripts/generate_kopi_chit.py.",
                )

    def test_assets_share_geometry_and_accessibility_contract(self):
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                source = path.read_text(encoding="utf-8")
                root = ET.fromstring(source)
                self.assertEqual(
                    root.attrib.get("viewBox"), f"0 0 {chit.WIDTH} {chit.HEIGHT}"
                )
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
                self.assertNotIn('href="', source)
                self.assertNotIn("https://", source)
                self.assertNotIn('src="//', source)
                self.assertNotIn('href="//', source)

    def test_the_paper_grain_is_generated_not_fetched(self):
        """GitHub serves this through a proxy that blocks external requests, so
        a fetched texture would come out blank."""
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                source = path.read_text(encoding="utf-8")
                self.assertIn("feTurbulence", source)
                self.assertIn('filter="url(#grain)"', source)

    def test_nothing_animated_hides_itself_at_rest(self):
        """The resting frame has to be the finished frame.

        An earlier version poured coffee into a glass from below. It looked
        right in a live browser and rendered an empty glass everywhere the
        animation was not running, because a renderer parked at t=0 sits on the
        from frame whether or not a fill-mode is set.
        """
        for theme, path in ASSET_PATHS.items():
            source = path.read_text(encoding="utf-8")
            with self.subTest(theme=theme, check="no backwards fill-mode"):
                for shorthand in re.findall(r"animation:\s*([^;]+);", source):
                    self.assertNotRegex(shorthand, r"\b(both|backwards)\b")

            animated = set(re.findall(r"\.([a-z0-9-]+)\s*\{[^}]*animation:", source))
            hooks = set(re.findall(r"\.([a-z0-9-]+)\s*\{\s*animation: none", source))
            self.assertTrue(hooks, "reduced motion switches nothing off")
            for name in animated - hooks:
                for attr in re.findall(
                    r'class="([^"]*\b' + re.escape(name) + r'\b[^"]*)"', source
                ):
                    with self.subTest(theme=theme, animated=name):
                        self.assertTrue(
                            hooks & set(attr.split()),
                            f'class="{attr}" animates with no reduced motion hook',
                        )

    def test_the_two_variants_differ_only_in_colour(self):
        light = ASSET_PATHS["light"].read_text(encoding="utf-8")
        dark = ASSET_PATHS["dark"].read_text(encoding="utf-8")
        self.assertNotEqual(light, dark)
        for key, value in chit.palette("light").items():
            light = light.replace(value, f"${key}")
        for key, value in chit.palette("dark").items():
            dark = dark.replace(value, f"${key}")
        self.assertEqual(light, dark)

    def test_no_colour_is_spelled_twice_within_a_theme(self):
        for theme in ("light", "dark"):
            with self.subTest(theme=theme):
                values = list(chit.palette(theme).values())
                self.assertEqual(len(values), len(set(values)))

    def test_every_palette_token_is_actually_used(self):
        for theme in ("light", "dark"):
            source = ASSET_PATHS[theme].read_text(encoding="utf-8")
            for key, value in chit.palette(theme).items():
                with self.subTest(theme=theme, token=key):
                    self.assertIn(value, source)


class NumbersTests(unittest.TestCase):
    """The figures have to be the ones the committed data actually supports."""

    def setUp(self):
        self.committed = json.loads(STATS_FILE.read_text(encoding="utf-8"))

    def test_the_hero_is_the_year_total(self):
        expected = f'{self.committed["total_contributions"]:,}'
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                hero = re.search(r'class="hero">([^<]+)<', path.read_text(encoding="utf-8"))
                self.assertIsNotNone(hero)
                self.assertEqual(hero.group(1), expected)

    def test_every_figure_matches_the_committed_data(self):
        values = dict(
            (label, value) for value, label in chit.figures(self.committed)
        )
        self.assertEqual(
            values["LONGEST STREAK"], chit.days_label(self.committed["longest_run"])
        )
        self.assertEqual(
            values["CURRENT STREAK"], chit.days_label(self.committed["current_run"])
        )
        self.assertEqual(
            values["BUSIEST DAY"], f'{max(self.committed["daily"]):,}'
        )
        active = sum(1 for day in self.committed["daily"][-30:] if day > 0)
        self.assertEqual(values[f"ACTIVE, LAST {chit.SPARK_DAYS} DAYS"], f"{active}/30")

    def test_all_four_figures_reach_the_card(self):
        for theme in ASSET_PATHS:
            rendered = drawn(theme)
            for value, label in chit.figures(self.committed):
                with self.subTest(theme=theme, label=label):
                    self.assertIn(value, rendered)
                    self.assertIn(label, rendered)

    def test_the_busiest_day_is_the_peak_of_the_whole_window(self):
        self.assertEqual(chit.busiest_day(stats(daily=[1, 90, 4])), 90)
        self.assertEqual(chit.busiest_day(stats(daily=[])), 0)

    def test_rate_is_reported_over_the_recent_window_not_the_year(self):
        """45 of 366 would read as dormant on an account that was simply new.

        666 of 726 commits landed in the final month, so the year ratio
        describes a period this account barely existed for.
        """
        payload = stats(daily=[0] * 336 + [1] * 30, days_active=30, days_total=366)
        self.assertEqual(chit.recent_active(payload), 30)
        year_ratio = f'{payload["days_active"]}/{payload["days_total"]}'
        self.assertNotIn(year_ratio, chit.render_chit("light", payload))

    def test_one_day_is_not_pluralised(self):
        self.assertEqual(chit.days_label(1), "1 day")
        self.assertEqual(chit.days_label(0), "0 days")
        self.assertIn(">1 day<", chit.render_chit("light", stats(longest_run=1)))

    def test_large_counts_get_thousands_separators(self):
        self.assertIn("12,345", chit.render_chit("light", stats(total_contributions=12345)))


class SparkTests(unittest.TestCase):
    def test_the_chart_always_plots_thirty_points(self):
        for daily in ([], [5], list(range(400))):
            with self.subTest(days=len(daily)):
                self.assertEqual(
                    len(chit.spark_points(stats(daily=daily))), chit.SPARK_DAYS
                )

    def test_a_short_history_is_padded_at_the_front_not_the_back(self):
        padded = chit.recent(stats(daily=[4, 5]))
        self.assertEqual(padded[-2:], [4, 5])
        self.assertEqual(padded[:-2], [0] * 28)

    def test_the_chart_spans_the_full_width_and_stays_on_its_baseline(self):
        points = chit.spark_points(stats())
        self.assertAlmostEqual(points[0][0], chit.SPARK_L)
        self.assertAlmostEqual(points[-1][0], chit.SPARK_R)
        for _, y in points:
            self.assertLessEqual(y, chit.SPARK_BASE)
            self.assertGreaterEqual(y, chit.SPARK_BASE - chit.SPARK_H)

    def test_a_silent_month_draws_a_flat_line_not_a_division_by_zero(self):
        points = chit.spark_points(stats(daily=[0] * 366))
        self.assertEqual({round(y, 6) for _, y in points}, {chit.SPARK_BASE})


class LastPushedTests(unittest.TestCase):
    def test_the_footer_reads_naturally_at_every_distance(self):
        for daily, expected in (
            ([1, 1, 1], "TODAY"),
            ([1, 1, 0], "YESTERDAY"),
            ([1, 0, 0], "2 DAYS AGO"),
            ([0, 0, 0], "NOT YET"),
            ([], "NOT YET"),
        ):
            with self.subTest(daily=daily):
                self.assertEqual(chit.served_label(stats(daily=daily)), expected)

    def test_the_gap_is_counted_back_from_the_window_not_from_today(self):
        """The label describes the data the card was built from, so a stale
        stats file cannot quietly start lying."""
        self.assertEqual(chit.days_since_served(stats(daily=[5] + [0] * 9)), 9)


class LayoutTests(unittest.TestCase):
    def test_the_hero_label_clears_the_descenders_above_it(self):
        """Georgia sets old style figures, so 3, 4, 7 and 9 drop below the
        baseline and the label collided with them at the first spacing."""
        self.assertGreaterEqual(chit.HERO_LABEL_Y - chit.HERO_Y, 32)

    def test_the_four_columns_do_not_collide(self):
        for left, right in zip(chit.COLUMNS, chit.COLUMNS[1:]):
            with self.subTest(column=left):
                self.assertGreaterEqual(right - left, 180)
        self.assertLess(chit.COLUMNS[-1], chit.PAD_R)

    def test_the_hero_column_does_not_run_under_the_chart(self):
        self.assertLess(chit.PAD_L + 300, chit.SPARK_L + 20)

    def test_everything_sits_inside_the_chit(self):
        self.assertLess(chit.FIGURE_LABEL_Y, chit.FOOTER_Y)
        self.assertLess(chit.FOOTER_Y, chit.CHIT_BOTTOM)
        self.assertLess(chit.CHIT_BOTTOM + chit.TOOTH_DROP, chit.HEIGHT)
        self.assertLess(chit.SPARK_BASE, chit.FIGURE_Y)


class RenderingTests(unittest.TestCase):
    def test_the_render_is_pure_and_repeatable(self):
        payload = stats()
        self.assertEqual(
            chit.render_chit("dark", payload), chit.render_chit("dark", payload)
        )
        self.assertEqual(payload, stats(), "render_chit mutated its input")

    def test_a_silent_account_still_renders_valid_markup(self):
        source = chit.render_chit(
            "light",
            stats(total_contributions=0, longest_run=0, current_run=0, daily=[0] * 366),
        )
        self.assertIsNone(NON_FINITE.search(source))
        ET.fromstring(source)
        self.assertIn("NOT YET", source)

    def test_an_empty_window_still_renders_valid_markup(self):
        ET.fromstring(
            chit.render_chit(
                "light",
                stats(
                    total_contributions=0,
                    days_total=0,
                    longest_run=0,
                    current_run=0,
                    daily=[],
                ),
            )
        )

    def test_the_date_is_formatted_without_depending_on_locale(self):
        self.assertIn("04 AUG 2026", chit.render_chit("light", stats()))
        self.assertIn(
            "01 JAN 2027", chit.render_chit("light", stats(generated_on="2027-01-01"))
        )

    def test_the_discarded_designs_stay_discarded(self):
        """Every shape tried and thrown out, so none of them creeps back."""
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                source = path.read_text(encoding="utf-8")
                for gone in (
                    "THE PAST YEAR",
                    "THE YEAR IN CUPS",
                    "HOW THE WEEK POURS",
                    "HOW THE WEEK SPLITS",
                    "THE COUNTER",
                    "rest day",
                    "footprint",
                    "tumbler",
                    "straw",
                    'class="ice"',
                ):
                    self.assertNotIn(gone, source)


class SharedSourceTests(unittest.TestCase):
    def test_the_signboard_strip_is_built_from_the_shared_stack(self):
        rendered = generate_kopi_sign.render_svg("light")
        for name, _ in generate_kopi_sign.STACK:
            self.assertIn(name, rendered)


if __name__ == "__main__":
    unittest.main()
