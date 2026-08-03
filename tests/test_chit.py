from pathlib import Path
import json
import re
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_kopi_chit  # noqa: E402
import generate_kopi_sign  # noqa: E402

ASSET_PATHS = {
    "dark": ROOT / "assets" / "kopi-chit-dark.svg",
    "light": ROOT / "assets" / "kopi-chit-light.svg",
}

STATS_FILE = ROOT / "data" / "stats.json"

# Python renders a non-finite float as nan/inf, and \b keeps "infinite" in the
# animation shorthand from tripping this.
NON_FINITE = re.compile(r"\b(nan|-?inf(inity)?)\b", re.IGNORECASE)


def stats(**overrides):
    base = {
        "login": "Kopi-O-Kosong-Beng",
        "generated_on": "2026-08-04",
        "window_start": "2025-08-03",
        "window_end": "2026-08-03",
        "total_contributions": 412,
        "days_active": 49,
        "days_total": 366,
        "longest_run": 7,
        "current_run": 2,
        "recent": [0, 1, 3, 0, 0, 2, 5, 0, 0, 0, 1, 4, 0, 0, 2] * 2,
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
                    generate_kopi_chit.render_chit(theme, committed),
                    "Asset has drifted. Re-run scripts/generate_kopi_chit.py.",
                )

    def test_assets_share_geometry_and_accessibility_contract(self):
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                source = path.read_text(encoding="utf-8")
                root = ET.fromstring(source)
                self.assertEqual(root.attrib.get("viewBox"), "0 0 900 360")
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

            animated = set(re.findall(r"\.([a-z-]+)\s*\{[^}]*animation:", source))
            hooks = set(re.findall(r"\.([a-z-]+)\s*\{\s*animation: none", source))
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
        for key, value in generate_kopi_chit.palette("light").items():
            light = light.replace(value, f"${key}")
        for key, value in generate_kopi_chit.palette("dark").items():
            dark = dark.replace(value, f"${key}")
        self.assertEqual(light, dark)

    def test_no_colour_is_spelled_twice_within_a_theme(self):
        """Two keys sharing a hex would make the strip above substitute the
        wrong name in one file and pass or fail for the wrong reason."""
        for theme in ("light", "dark"):
            with self.subTest(theme=theme):
                values = list(generate_kopi_chit.palette(theme).values())
                self.assertEqual(len(values), len(set(values)))

    def test_every_palette_token_is_actually_used(self):
        for theme in ("light", "dark"):
            for key, value in generate_kopi_chit.palette(theme).items():
                with self.subTest(theme=theme, token=key):
                    self.assertIn(
                        value, ASSET_PATHS[theme].read_text(encoding="utf-8")
                    )

    def test_assets_carry_the_chit_copy(self):
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                root = ET.fromstring(path.read_text(encoding="utf-8"))
                rendered = "".join(root.itertext())
                for label in (
                    "KOPI O KOSONG BENG",
                    "ORDER #",
                    "commits, past year",
                    "longest run",
                    "days brewed",
                    "LAST 30 DAYS",
                    "TODAY'S BREW",
                    "no sugar",
                ):
                    self.assertIn(label, rendered)

    def test_every_stack_entry_is_stamped_on_an_ice_cube(self):
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                root = ET.fromstring(path.read_text(encoding="utf-8"))
                rendered = "".join(root.itertext())
                for _, short in generate_kopi_sign.STACK:
                    self.assertIn(short, rendered)


class ChitRenderingTests(unittest.TestCase):
    def render(self, **overrides):
        return generate_kopi_chit.render_chit("light", stats(**overrides))

    def test_a_silent_year_renders_without_dividing_by_zero(self):
        source = self.render(
            total_contributions=0,
            days_active=0,
            longest_run=0,
            current_run=0,
            recent=[0] * 30,
        )
        self.assertIsNone(NON_FINITE.search(source), "non finite number reached the SVG")
        ET.fromstring(source)

    def test_a_full_year_fills_the_glass_to_the_brim(self):
        empty = generate_kopi_chit.surface_y(0.0)
        full = generate_kopi_chit.surface_y(1.0)
        self.assertLess(full, empty, "a fuller glass must have a higher surface")
        self.assertEqual(full, generate_kopi_chit.GLASS_TOP_LEVEL)
        self.assertEqual(empty, generate_kopi_chit.GLASS_BOTTOM_LEVEL)

    def test_the_coffee_level_tracks_the_share_of_days_brewed(self):
        half = generate_kopi_chit.fill_fraction(stats(days_active=183, days_total=366))
        self.assertAlmostEqual(half, 0.5)
        self.assertEqual(
            generate_kopi_chit.fill_fraction(stats(days_active=0, days_total=0)), 0.0
        )

    def test_bar_heights_scale_to_the_busiest_day_and_never_vanish(self):
        heights = generate_kopi_chit.bar_heights([0, 5, 10])
        self.assertEqual(heights[2], generate_kopi_chit.BAR_MAX)
        self.assertEqual(heights[0], generate_kopi_chit.BAR_MIN)
        self.assertLess(heights[1], heights[2])
        self.assertGreater(heights[1], heights[0])

    def test_a_flat_series_draws_a_baseline_rather_than_full_height_bars(self):
        self.assertEqual(
            generate_kopi_chit.bar_heights([0] * 30), [generate_kopi_chit.BAR_MIN] * 30
        )

    def test_large_counts_get_thousands_separators(self):
        source = self.render(total_contributions=12345)
        self.assertIn("12,345", source)

    def test_one_day_is_not_pluralised(self):
        self.assertIn("1 day<", self.render(longest_run=1))
        self.assertIn("2 days<", self.render(longest_run=2))

    def test_markup_in_a_stack_label_is_escaped_and_the_svg_still_parses(self):
        source = generate_kopi_chit.render_chit(
            "light", stats(), stack=(("ampersand & angle", "a&<b"),)
        )
        self.assertNotIn("a&<b", source)
        self.assertIn("a&amp;&lt;b", source)
        ET.fromstring(source)

    def test_the_render_is_pure_and_repeatable(self):
        payload = stats()
        first = generate_kopi_chit.render_chit("dark", payload)
        second = generate_kopi_chit.render_chit("dark", payload)
        self.assertEqual(first, second)
        self.assertEqual(payload, stats(), "render_chit mutated its input")

    def test_the_date_is_formatted_without_depending_on_locale(self):
        self.assertIn("04 AUG 2026", self.render(generated_on="2026-08-04"))
        self.assertIn("01 JAN 2027", self.render(generated_on="2027-01-01"))


class SharedSourceTests(unittest.TestCase):
    def test_the_signboard_strip_is_built_from_the_same_stack(self):
        line = generate_kopi_sign.render_svg("light")
        for name, _ in generate_kopi_sign.STACK:
            self.assertIn(name, line)

    def test_the_signboard_description_still_names_every_stack_entry(self):
        """The desc is hand written prose, so it can silently fall behind."""
        desc = generate_kopi_sign.render_svg("light").lower()
        alias = {"c++": "c++", "typescript": "typescript", "gcp": "gcp"}
        for name, _ in generate_kopi_sign.STACK:
            self.assertIn(alias.get(name, name), desc)


if __name__ == "__main__":
    unittest.main()
