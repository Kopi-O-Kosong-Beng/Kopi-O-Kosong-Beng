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
                    "days active",
                    "THE LAST THIRTY DAYS",
                    "COUNTING SINCE",
                    "TODAY",
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
                    "footprint",
                    "stain",
                    "clipPath",
                ):
                    self.assertNotIn(gone, source)

    def test_the_second_glass_is_gone_for_good(self):
        """The signboard already draws the glass and already prints the stack,
        so a glass here repeated both the picture and the words."""
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                source = path.read_text(encoding="utf-8")
                for gone in ("straw", "clipPath", "TODAY&#39;S BREW", "class=\"ice\""):
                    self.assertNotIn(gone, source)


class BarTests(unittest.TestCase):
    def test_thirty_bars_are_drawn_whatever_the_history(self):
        for daily in ([], [1], list(range(400))):
            with self.subTest(days=len(daily)):
                self.assertEqual(len(chit.recent(stats(daily=daily))), chit.BARS)
                self.assertEqual(chit.bars(stats(daily=daily)).count("<rect"), chit.BARS)

    def test_the_newest_day_is_the_rightmost_bar(self):
        self.assertEqual(chit.recent(stats(daily=[9, 8, 7]))[-1], 7)

    def test_a_short_history_is_padded_at_the_front_not_the_back(self):
        padded = chit.recent(stats(daily=[4, 5]))
        self.assertEqual(padded[-2:], [4, 5])
        self.assertEqual(padded[:-2], [0] * 28)

    def test_heights_scale_to_the_busiest_day_and_never_vanish(self):
        heights = chit.bar_heights([0, 5, 10])
        self.assertEqual(heights[2], chit.BAR_MAX)
        self.assertEqual(heights[0], chit.BAR_MIN)
        self.assertLess(heights[1], heights[2])
        self.assertGreater(heights[1], heights[0])

    def test_length_carries_the_value_linearly(self):
        """A bar is read by length, unlike a circle, which is read by area."""
        half = chit.bar_heights([5, 10])[0] - chit.BAR_MIN
        full = chit.bar_heights([5, 10])[1] - chit.BAR_MIN
        self.assertAlmostEqual(full / half, 2.0)

    def test_a_flat_month_draws_a_baseline_not_full_height_bars(self):
        self.assertEqual(chit.bar_heights([0] * 30), [chit.BAR_MIN] * 30)

    def test_an_idle_day_is_drawn_in_the_quiet_colour(self):
        drawn = chit.bars(stats(daily=[0, 0, 4]))
        self.assertEqual(drawn.count('class="bar-idle"'), 29)

    def test_the_axis_names_the_day_the_leftmost_bar_stands_for(self):
        # Thirty bars ending 03 AUG 2026 start on 05 JUL 2026.
        self.assertEqual(chit.window_label(stats(window_end="2026-08-03")), "05 JUL 2026")

    def test_the_bars_stay_inside_the_printed_area(self):
        pitch = (chit.PAD_R - chit.PAD_L) / chit.BARS
        self.assertLessEqual(chit.PAD_L + (chit.BARS - 1) * pitch + (pitch - 8), chit.PAD_R)
        self.assertGreater(pitch - 8, 4, "bars would be hairlines")


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

    def test_the_gauge_tracks_the_share_of_days_brewed(self):
        self.assertAlmostEqual(
            chit.fill_fraction(stats(days_active=183, days_total=366)), 0.5
        )
        self.assertEqual(chit.fill_fraction(stats(days_active=0, days_total=0)), 0.0)
        half = self.render(days_active=183, days_total=366)
        self.assertIn(f'class="gauge" x="{chit.GAUGE_X}"', half)
        self.assertIn(f'width="{chit.num(chit.GAUGE_W / 2)}"', half)

    def test_an_empty_gauge_draws_no_fill(self):
        self.assertIn(
            f'class="gauge" x="{chit.GAUGE_X}" y="168" width="0"',
            self.render(days_active=0),
        )

    def test_large_counts_get_thousands_separators(self):
        self.assertIn("12,345", self.render(total_contributions=12345))

    def test_one_day_is_not_pluralised(self):
        self.assertIn("1 day<", self.render(longest_run=1))
        self.assertIn("2 days<", self.render(longest_run=2))

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
