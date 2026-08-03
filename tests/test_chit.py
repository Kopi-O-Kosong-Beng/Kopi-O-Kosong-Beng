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

    def test_nothing_animated_hides_itself_at_rest(self):
        """The resting frame has to be the finished frame.

        An earlier version poured the coffee in from below the glass. It looked
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
                    "commits, past year",
                    "longest streak",
                    "busiest 10 days",
                    "HOW THE WEEK POURS",
                    "COUNTING SINCE",
                    "MON",
                    "SUN",
                ):
                    self.assertIn(label, rendered)

    def test_the_discarded_designs_stay_discarded(self):
        """Three shapes were tried and thrown out, each for its own reason.

        A second glass repeated the signboard's picture and its words. A grid
        of small squares is the graphic GitHub already draws on the same page.
        Twelve monthly cup rings were mostly empty holes, because nine of the
        twelve months in this data have nothing in them.
        """
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                source = path.read_text(encoding="utf-8")
                for gone in (
                    "THE PAST YEAR",
                    "THE YEAR IN CUPS",
                    "THE LAST THIRTY DAYS",
                    "TRADING DAYS",
                    "footprint",
                    "stain",
                    "straw",
                ):
                    self.assertNotIn(gone, source)

    def test_no_second_hero_glass_competes_with_the_signboard(self):
        """Seven small tumblers are data marks, and that is fine.

        What is banned is a second *detailed* glass, the kind the signboard
        already draws: a straw, ice cubes, condensation, and the stack stamped
        on the ice. That version repeated the signboard's picture and its words
        at the same time, and put two cups on one profile.
        """
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                source = path.read_text(encoding="utf-8")
                for gone in (
                    "straw",
                    "TODAY&#39;S BREW",
                    'class="ice"',
                    "drop motion",
                ):
                    self.assertNotIn(gone, source)
                self.assertEqual(source.count('class="tumbler"'), 7)


class InsightTests(unittest.TestCase):
    """The card has to say something the profile page does not already say."""

    def test_weekday_totals_start_on_monday_and_keep_every_day(self):
        # 2025-08-03 is a Sunday, so a single day lands in the last slot.
        self.assertEqual(
            chit.weekday_totals(stats(window_start="2025-08-03", daily=[7])),
            [0, 0, 0, 0, 0, 0, 7],
        )
        # A full week of ones puts one in every slot.
        self.assertEqual(
            chit.weekday_totals(stats(window_start="2025-08-04", daily=[1] * 7)),
            [1] * 7,
        )

    def test_weekday_totals_sum_to_the_whole_window(self):
        self.assertEqual(sum(chit.weekday_totals(stats())), sum(DAILY))

    def test_the_burst_share_is_the_top_days_over_the_total(self):
        # Ten days of ten, ninety days of one: 100 of 190.
        payload = stats(daily=[10] * 10 + [1] * 90)
        self.assertAlmostEqual(chit.burst_share(payload), 100 / 190)

    def test_the_burst_share_of_a_silent_year_is_zero_not_a_crash(self):
        self.assertEqual(chit.burst_share(stats(daily=[0] * 366)), 0.0)
        self.assertEqual(chit.burst_share(stats(daily=[])), 0.0)

    def test_a_rest_day_is_only_claimed_when_it_is_really_quiet(self):
        """An evenly worked week must not get an arbitrary day labelled."""
        even = stats(window_start="2025-08-04", daily=[5] * 7)
        self.assertIsNone(chit.rest_day(even))

        # Six busy weekdays and one near dead one: 2025-08-08 is a Friday.
        lopsided = stats(window_start="2025-08-04", daily=[40, 40, 40, 40, 1, 40, 40])
        self.assertEqual(chit.rest_day(lopsided), 4)
        self.assertEqual(chit.WEEKDAYS[4], "FRI")

    def test_a_silent_year_claims_no_rest_day(self):
        self.assertIsNone(chit.rest_day(stats(daily=[0] * 366)))

    def test_the_rest_day_is_tagged_and_drawn_in_the_quiet_colour(self):
        drawn = chit.weekday_glasses(
            stats(window_start="2025-08-04", daily=[40, 40, 40, 40, 1, 40, 40])
        )
        self.assertEqual(drawn.count('class="pour-quiet"'), 1)
        self.assertEqual(drawn.count("rest day"), 1)

    def test_no_rest_day_means_no_tag_at_all(self):
        drawn = chit.weekday_glasses(stats(window_start="2025-08-04", daily=[5] * 7))
        self.assertNotIn("rest day", drawn)
        self.assertNotIn("pour-quiet", drawn)

    def test_the_streak_carries_the_date_it_ended(self):
        # Four in a row from 2026-01-05, then a gap.
        payload = stats(
            window_start="2026-01-05", daily=[1, 1, 1, 1, 0, 1], longest_run=4
        )
        self.assertEqual(chit.best_run_end(payload), date(2026, 1, 8))
        self.assertEqual(chit.streak_value(payload), "4 days to 08 JAN")

    def test_a_streak_with_no_history_still_renders_a_value(self):
        self.assertEqual(chit.streak_value(stats(daily=[], longest_run=0)), "0 days")

    def test_the_pour_level_carries_the_value_linearly(self):
        """Level is a length up the glass, unlike a circle read by its area."""
        half, full = chit.pour_levels([5, 10])
        self.assertAlmostEqual(full / half, 2.0)
        self.assertEqual(full, 1.0)
        self.assertEqual(chit.surface_y(1.0), chit.GLASS_FULL)
        self.assertEqual(chit.surface_y(0.0), chit.GLASS_EMPTY)

    def test_a_silent_week_pours_nothing_rather_than_dividing_by_zero(self):
        self.assertEqual(chit.pour_levels([0] * 7), [0.0] * 7)
        self.assertNotIn("class=\"pour", chit.weekday_glasses(stats(daily=[0] * 366)))

    def test_seven_glasses_are_drawn_whatever_the_history(self):
        for daily in ([], [1], list(range(400))):
            with self.subTest(days=len(daily)):
                drawn = chit.weekday_glasses(stats(daily=daily))
                self.assertEqual(drawn.count('class="tumbler"'), 7)
                self.assertEqual(drawn.count("<clipPath"), 7)

    def test_each_glass_clips_its_own_pour(self):
        """A shared clip id would pour every glass to the same level."""
        drawn = chit.weekday_glasses(stats())
        ids = re.findall(r'<clipPath id="([^"]+)"', drawn)
        self.assertEqual(len(ids), len(set(ids)))

    def test_the_glasses_stay_inside_the_printed_area(self):
        pitch = (chit.PAD_R - chit.PAD_L) / 7
        self.assertLess(2 * chit.GLASS_TOP_HW, pitch, "neighbouring glasses touch")
        self.assertGreaterEqual(chit.PAD_L + 0.5 * pitch - chit.GLASS_TOP_HW, chit.PAD_L)
        self.assertLessEqual(chit.PAD_L + 6.5 * pitch + chit.GLASS_TOP_HW, chit.PAD_R)


class ChitRenderingTests(unittest.TestCase):
    def render(self, **overrides):
        return chit.render_chit("light", stats(**overrides))

    def test_a_silent_year_renders_without_dividing_by_zero(self):
        source = self.render(
            total_contributions=0,
            days_active=0,
            longest_run=0,
            current_run=0,
            daily=[0] * 366,
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
                current_run=0,
                daily=[],
            )
        )

    def test_the_gauge_tracks_the_burst_share(self):
        # Ten days of ten against ten days of one: 100 of 110.
        payload = stats(daily=[10] * 10 + [1] * 10)
        drawn = chit.render_chit("light", payload)
        self.assertIn(f'class="gauge" x="{chit.GAUGE_X}"', drawn)
        self.assertIn(
            f'width="{chit.num(chit.GAUGE_W * (100 / 110))}"',
            drawn,
        )
        self.assertIn("91% of the year", drawn)

    def test_an_empty_gauge_draws_no_fill(self):
        self.assertIn(
            f'class="gauge" x="{chit.GAUGE_X}" y="168" width="0"',
            self.render(daily=[0] * 366),
        )

    def test_large_counts_get_thousands_separators(self):
        self.assertIn("12,345", self.render(total_contributions=12345))

    def test_one_day_is_not_pluralised(self):
        self.assertIn("1 day to ", self.render(longest_run=1))
        self.assertIn("2 days to ", self.render(longest_run=2))
        self.assertEqual(chit.days_label(1), "1 day")
        self.assertEqual(chit.days_label(0), "0 days")

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
