from datetime import date
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

# Python renders a non-finite float as nan/inf, and \b keeps "infinite" in the
# animation shorthand from tripping this.
NON_FINITE = re.compile(r"\b(nan|-?inf(inity)?)\b", re.IGNORECASE)

DAILY = [(index * 7) % 11 for index in range(366)]


def stats(**overrides):
    base = {
        "login": "Kopi-O-Kosong-Beng",
        "generated_on": "2026-08-04",
        # A Sunday, which is where GitHub starts the calendar.
        "window_start": "2025-08-03",
        "window_end": "2026-08-03",
        "total_contributions": sum(DAILY),
        "days_active": sum(1 for day in DAILY if day > 0),
        "days_total": len(DAILY),
        "longest_run": 23,
        "current_run": 4,
        "daily": list(DAILY),
    }
    base.update(overrides)
    return base


class ChitAssetTests(unittest.TestCase):
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
        over data/stats.json, so a stale asset and a hand edited asset both fail
        exactly as they did for the signboard.
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
        """The texture is a filter, not a bitmap. GitHub serves this through a
        proxy that blocks external requests, so an <image> would come out blank.
        """
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                source = path.read_text(encoding="utf-8")
                self.assertIn("feTurbulence", source)
                self.assertIn('filter="url(#grain)"', source)
                self.assertNotIn("<image", source.lower())

    def test_nothing_animated_hides_itself_at_rest(self):
        """The resting frame has to be the finished frame.

        An earlier version poured coffee into a glass from below. It looked
        right in a live browser and rendered an empty glass everywhere the
        animation was not actually running, because a renderer parked at t=0
        sits on the from frame whether or not a fill-mode is set. Two rules keep
        that from coming back: no animation may declare a backwards fill-mode,
        and every animated element must carry a class the reduced motion block
        can switch off.
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
        """Two keys sharing a hex would make the strip above substitute the
        wrong name in one file and pass or fail for the wrong reason."""
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

    def test_assets_carry_the_chit_copy(self):
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                root = ET.fromstring(path.read_text(encoding="utf-8"))
                rendered = "".join(root.itertext())
                for label in (
                    "KOPI O KOSONG BENG",
                    "ORDER #",
                    "COMMITS, PAST YEAR",
                    "THE LAST 30 DAYS",
                    "ACTIVE DAYS",
                ):
                    self.assertIn(label, rendered)

    def test_the_derived_finding_leads_and_the_totals_do_not(self):
        """The hero has to be the one number GitHub does not already print.

        Totals and streaks are shown on the profile page directly above this
        image, so leading with them made the card decoration with a torn edge.
        """
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                source = path.read_text(encoding="utf-8")
                hero = re.search(r'class="hero">([^<]+)<', source)
                self.assertIsNotNone(hero, "no hero number on the card")
                self.assertTrue(hero.group(1).strip())
                self.assertIn('class="ring"', source)
                # The hero is set larger than any supporting figure.
                sizes = {
                    name: float(size)
                    for name, size in re.findall(
                        r"\.(hero|figure)\s*\{[^}]*font-size:\s*([\d.]+)px", source
                    )
                }
                self.assertGreater(sizes["hero"], 1.4 * sizes["figure"])

    def test_the_discarded_designs_stay_discarded(self):
        """Four shapes were tried and thrown out, each for its own reason.

        A second detailed glass repeated the signboard's picture and its words.
        A grid of small squares is the graphic GitHub already draws on the same
        page. Twelve monthly cup rings were mostly empty holes, because nine of
        the twelve months in this data have nothing in them. Seven glasses, one
        per weekday, turned the card into a dashboard of small multiples with
        most of each glass left as empty outline.
        """
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                source = path.read_text(encoding="utf-8")
                for gone in (
                    "THE PAST YEAR",
                    "THE YEAR IN CUPS",
                    "HOW THE WEEK POURS",
                    "HOW THE WEEK SPLITS",
                    "seg-quiet",
                    "rest day",
                    "footprint",
                    "stain",
                    "tumbler",
                    "straw",
                    'class="ice"',
                ):
                    self.assertNotIn(gone, source)


class InsightTests(unittest.TestCase):
    """The card has to say something the profile page does not already say."""

    def test_the_streak_keeps_its_date_in_the_label_not_the_figure(self):
        """The date must not swell the figure into rivalling the hero."""
        payload = stats(
            window_start="2026-01-05", daily=[1, 1, 1, 1, 0, 1], longest_run=4
        )
        self.assertEqual(chit.best_run_end(payload), date(2026, 1, 8))
        self.assertEqual(chit.streak_label(payload), "LONGEST STREAK, TO 08 JAN")
        self.assertEqual(chit.streak_label(stats(daily=[])), "LONGEST STREAK")


class FramingTests(unittest.TestCase):
    """The window is the whole argument.

    Over 366 days this account reads as dormant: 45 active days, because it was
    genuinely quiet until the final month. Over 30 days it reads as someone
    shipping most days. Both are true, and publishing the year ratio told a
    visitor the opposite of the truth about how this person works now.
    """

    def test_the_year_ratio_never_reaches_the_card(self):
        committed = json.loads(STATS_FILE.read_text(encoding="utf-8"))
        year_ratio = f'{committed["days_active"]}/{committed["days_total"]}'
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                self.assertNotIn(year_ratio, path.read_text(encoding="utf-8"))

    def test_a_dormant_start_does_not_drag_down_the_headline(self):
        """Eleven quiet months then a month of daily work. The card has to read
        the last thirty days, not average them against the dead year."""
        daily = [0] * 336 + [4] * 30
        payload = stats(
            daily=daily,
            days_total=len(daily),
            days_active=30,
            total_contributions=sum(daily),
            longest_run=30,
            current_run=30,
        )
        hero, _ = chit.hero_and_support(payload)
        self.assertIn(hero["key"], ("recent", "running"))
        self.assertGreaterEqual(hero["gauge"], 0.9)

    def test_a_lapsed_account_is_not_flattered_by_the_recent_window(self):
        """The reverse has to hold too: busy last year, nothing this month."""
        daily = [4] * 336 + [0] * 30
        payload = stats(
            daily=daily,
            days_total=len(daily),
            days_active=336,
            total_contributions=sum(daily),
            longest_run=336,
            current_run=0,
        )
        hero, _ = chit.hero_and_support(payload)
        self.assertNotEqual(hero["key"], "recent")


class SustainabilityTests(unittest.TestCase):
    """The headline must survive a change of habit.

    A burst share is a striking headline at 57% and an embarrassing one at 19%.
    Hardcoding it would leave the card bragging about nothing a year from now,
    so every candidate is scored and the strongest one is promoted.
    """

    @staticmethod
    def shaped(daily, run=0, running=0):
        return stats(
            daily=daily,
            days_total=len(daily),
            days_active=sum(1 for day in daily if day > 0),
            total_contributions=sum(daily),
            longest_run=run,
            current_run=running,
        )

    def hero(self, daily, run=0, running=0):
        return chit.hero_and_support(self.shaped(daily, run, running))[0]

    def test_a_recently_active_account_leads_with_the_recent_window(self):
        self.assertEqual(self.hero([0] * 336 + [3] * 30, run=30)["key"], "recent")

    def test_a_long_current_run_can_outrank_the_recent_window(self):
        hero = self.hero([2] * 300 + [0] * 36 + [2] * 30, run=300, running=40)
        self.assertIn(hero["key"], ("running", "recent"))

    def test_a_silent_year_never_headlines_a_zero_percent(self):
        """max() keeps the first maximum, so the floor candidate is declared
        first and wins the all zero tie."""
        hero = self.hero([0] * 366)
        self.assertEqual(hero["key"], "total")
        self.assertEqual(hero["value"], "0")

    def test_the_dial_matches_the_headline_it_is_drawn_around(self):
        for daily, run in (([0] * 336 + [80] * 30, 30), ([2] * 300 + [0] * 66, 40)):
            with self.subTest(run=run):
                hero = self.hero(daily, run=run, running=run)
                self.assertGreaterEqual(hero["gauge"], 0.0)
                self.assertLessEqual(hero["gauge"], 1.0)

    def test_the_supports_never_repeat_the_hero(self):
        for daily, run in (([0] * 336 + [80] * 30, 30), ([2] * 366, 366), ([0] * 366, 0)):
            with self.subTest(total=sum(daily)):
                hero, support = chit.hero_and_support(self.shaped(daily, run, run))
                self.assertEqual(len(support), 2)
                self.assertNotIn(hero["key"], [entry["key"] for entry in support])
                self.assertEqual(len({entry["key"] for entry in support}), 2)

    def test_every_candidate_is_renderable_whichever_one_wins(self):
        for daily, run in (([0] * 366, 0), ([1] * 366, 366), ([0] * 336 + [80] * 30, 30)):
            with self.subTest(total=sum(daily)):
                ET.fromstring(chit.render_chit("dark", self.shaped(daily, run, run)))


class SparkTests(unittest.TestCase):
    def test_the_area_chart_always_plots_thirty_points(self):
        for daily in ([], [5], list(range(400))):
            with self.subTest(days=len(daily)):
                self.assertEqual(len(chit.spark_points(stats(daily=daily))), chit.SPARK_DAYS)

    def test_a_short_history_is_padded_at_the_front_not_the_back(self):
        padded = chit.recent(stats(daily=[4, 5]))
        self.assertEqual(padded[-2:], [4, 5])
        self.assertEqual(padded[:-2], [0] * 28)

    def test_the_chart_spans_the_full_width_and_never_leaves_the_baseline(self):
        points = chit.spark_points(stats())
        self.assertAlmostEqual(points[0][0], chit.SPARK_L)
        self.assertAlmostEqual(points[-1][0], chit.SPARK_R)
        for _, y in points:
            self.assertLessEqual(y, chit.SPARK_BASE)
            self.assertGreaterEqual(y, chit.SPARK_BASE - chit.SPARK_H)

    def test_a_silent_month_draws_a_flat_line_not_a_division_by_zero(self):
        points = chit.spark_points(stats(daily=[0] * 366))
        self.assertEqual({round(y, 6) for _, y in points}, {chit.SPARK_BASE})

    def test_the_dial_is_capped_short_of_a_full_turn(self):
        """An arc whose ends coincide is degenerate and renders as nothing."""
        self.assertIn(" 1 ", chit.ring_arc(1.0))
        self.assertTrue(chit.ring_arc(1.0).startswith("M "))
        ET.fromstring(f'<svg xmlns="http://www.w3.org/2000/svg"><path d="{chit.ring_arc(1.0)}"/></svg>')
        ET.fromstring(f'<svg xmlns="http://www.w3.org/2000/svg"><path d="{chit.ring_arc(0.0)}"/></svg>')




class ChitRenderingTests(unittest.TestCase):
    def render(self, **overrides):
        return chit.render_chit("light", stats(**overrides))

    def test_a_silent_year_renders_without_dividing_by_zero(self):
        source = self.render(
            total_contributions=0, days_active=0, longest_run=0, daily=[0] * 366
        )
        self.assertIsNone(NON_FINITE.search(source), "non finite number reached the SVG")
        ET.fromstring(source)

    def test_an_entirely_empty_window_still_renders_valid_markup(self):
        ET.fromstring(
            self.render(
                total_contributions=0,
                days_active=0,
                days_total=0,
                longest_run=0,
                daily=[],
            )
        )

    def test_large_counts_get_thousands_separators(self):
        self.assertIn("12,345", self.render(total_contributions=12345))

    def test_one_day_is_not_pluralised(self):
        self.assertIn(">1 day<", self.render(longest_run=1))
        self.assertIn(">2 days<", self.render(longest_run=2))

    def test_the_render_is_pure_and_repeatable(self):
        payload = stats()
        self.assertEqual(
            chit.render_chit("dark", payload), chit.render_chit("dark", payload)
        )
        self.assertEqual(payload, stats(), "render_chit mutated its input")

    def test_the_date_is_formatted_without_depending_on_locale(self):
        self.assertIn("04 AUG 2026", self.render(generated_on="2026-08-04"))
        self.assertIn("01 JAN 2027", self.render(generated_on="2027-01-01"))


class SharedSourceTests(unittest.TestCase):
    def test_the_signboard_strip_is_built_from_the_shared_stack(self):
        rendered = generate_kopi_sign.render_svg("light")
        for name, _ in generate_kopi_sign.STACK:
            self.assertIn(name, rendered)

    def test_the_signboard_description_still_names_every_stack_entry(self):
        """The desc is hand written prose, so it can silently fall behind."""
        desc = generate_kopi_sign.render_svg("light").lower()
        for name, _ in generate_kopi_sign.STACK:
            self.assertIn(name, desc)


if __name__ == "__main__":
    unittest.main()
