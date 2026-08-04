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
        "total_contributions": 726,
        "days_active": 45,
        "days_total": 366,
        "longest_run": 23,
        "current_run": 4,
        "daily": [0] * 336 + [3] * 30,
    }
    base.update(overrides)
    return base


class CounterAssetTests(unittest.TestCase):
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


class CounterCopyTests(unittest.TestCase):
    def rendered(self, theme):
        root = ET.fromstring(ASSET_PATHS[theme].read_text(encoding="utf-8"))
        return "".join(root.itertext())

    def test_every_entry_reaches_the_card_whole(self):
        for theme in ASSET_PATHS:
            rendered = self.rendered(theme)
            for entry in chit.COUNTER:
                with self.subTest(theme=theme, entry=entry["name"]):
                    self.assertIn(entry["name"], rendered)
                    self.assertIn(entry["line"], rendered)
                    self.assertIn(entry["note"], rendered)
                    for tag in entry["stack"]:
                        self.assertIn(tag, rendered)

    def test_the_card_says_what_each_thing_is_built_with(self):
        """The whole reason this card exists. The README lists the projects in
        prose and never says the stack, which is what a visitor scans for."""
        for entry in chit.COUNTER:
            with self.subTest(entry=entry["name"]):
                self.assertTrue(entry["stack"], "an entry with no stack tags")

    def test_the_card_carries_its_heading_and_the_live_line(self):
        for theme in ASSET_PATHS:
            rendered = self.rendered(theme)
            self.assertIn("THE COUNTER", rendered)
            self.assertIn("KOPI O KOSONG BENG", rendered)
            self.assertIn("LAST SERVED", rendered)


class NoScoreboardTests(unittest.TestCase):
    """This card must never drift back into an activity scoreboard.

    Commit counts, streaks and ratios are the weakest signal on a profile, and
    measured over a year this account reads as dormant because it genuinely was
    until recently. All of it was true and none of it helped.
    """

    def setUp(self):
        self.committed = json.loads(STATS_FILE.read_text(encoding="utf-8"))

    def rendered(self, theme):
        """Only what a reader actually sees.

        itertext() would sweep in the <style> block, whose keyframe stops are
        written as 0% and 100%, and the guard would fail on its own CSS.
        """
        source = ASSET_PATHS[theme].read_text(encoding="utf-8")
        return "\n".join(re.findall(r"<text[^>]*>([^<]*)</text>", source))

    def test_no_commit_total_reaches_the_card(self):
        total = str(self.committed["total_contributions"])
        for theme in ASSET_PATHS:
            with self.subTest(theme=theme):
                self.assertNotIn(total, self.rendered(theme))

    def test_no_streak_reaches_the_card(self):
        run = self.committed["longest_run"]
        for theme in ASSET_PATHS:
            with self.subTest(theme=theme):
                rendered = self.rendered(theme)
                self.assertNotIn(f"{run} day", rendered)
                self.assertNotIn("STREAK", rendered.upper())

    def test_no_year_ratio_reaches_the_card(self):
        ratio = f'{self.committed["days_active"]}/{self.committed["days_total"]}'
        for theme in ASSET_PATHS:
            with self.subTest(theme=theme):
                self.assertNotIn(ratio, self.rendered(theme))

    def test_no_percentage_reaches_the_card(self):
        for theme in ASSET_PATHS:
            with self.subTest(theme=theme):
                self.assertNotIn("%", self.rendered(theme))

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
                    "BUSIEST",
                    "rest day",
                    "footprint",
                    "tumbler",
                    "straw",
                    'class="ice"',
                    'class="ring"',
                    "spark",
                ):
                    self.assertNotIn(gone, source)


class LastServedTests(unittest.TestCase):
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
        """The label has to describe the data the card was built from, or a
        stale stats file would quietly start lying."""
        self.assertEqual(chit.days_since_served(stats(daily=[5] + [0] * 9)), 9)


class LayoutTests(unittest.TestCase):
    def test_no_row_separator_crosses_a_stack_chip(self):
        """The separators sat straight across the chips in the first cut."""
        for theme, path in ASSET_PATHS.items():
            source = path.read_text(encoding="utf-8")
            rules = [
                float(value)
                for value in re.findall(
                    rf'class="dot" d="M {chit.PAD_L} ([0-9.]+) H', source
                )
            ]
            bands = [
                (float(y), float(y) + chit.CHIP_H)
                for y in re.findall(r'class="chip" x="[0-9.]+" y="([0-9.]+)"', source)
            ]
            self.assertTrue(rules and bands)
            for rule in rules:
                for low, high in bands:
                    with self.subTest(theme=theme, rule=rule):
                        self.assertFalse(low <= rule <= high, "separator crosses a chip")

    def test_every_row_and_the_footer_sit_inside_the_chit(self):
        last = chit.ROW_TOP + (len(chit.COUNTER) - 1) * chit.ROW_H
        self.assertLess(last + 60, chit.FOOTER_Y)
        self.assertLess(chit.FOOTER_Y, chit.CHIT_BOTTOM)
        self.assertLess(chit.CHIT_BOTTOM + chit.TOOTH_DROP, chit.HEIGHT)

    def test_a_row_of_chips_never_runs_past_the_right_margin(self):
        for entry in chit.COUNTER:
            with self.subTest(entry=entry["name"]):
                width = sum(
                    len(tag) * chit.CHIP_CHAR + 2 * chit.CHIP_PAD
                    for tag in entry["stack"]
                ) + chit.CHIP_GAP * (len(entry["stack"]) - 1)
                self.assertLess(chit.PAD_L + width, chit.PAD_R)


class RenderingTests(unittest.TestCase):
    def test_the_render_is_pure_and_repeatable(self):
        payload = stats()
        self.assertEqual(
            chit.render_chit("dark", payload), chit.render_chit("dark", payload)
        )
        self.assertEqual(payload, stats(), "render_chit mutated its input")

    def test_a_silent_account_still_renders_valid_markup(self):
        source = chit.render_chit("light", stats(daily=[0] * 366))
        self.assertIsNone(NON_FINITE.search(source))
        ET.fromstring(source)
        self.assertIn("NOT YET", source)

    def test_markup_in_an_entry_is_escaped_and_the_svg_still_parses(self):
        original = chit.COUNTER
        try:
            chit.COUNTER = (
                {
                    "name": "a & b",
                    "note": "LIVE",
                    "line": "<script>alert(1)</script>",
                    "stack": ("c++", "a<b"),
                },
            )
            source = chit.render_chit("light", stats())
            self.assertNotIn("<script>", source)
            self.assertIn("&amp;", source)
            ET.fromstring(source)
        finally:
            chit.COUNTER = original

    def test_the_date_is_formatted_without_depending_on_locale(self):
        self.assertIn("04 AUG 2026", chit.render_chit("light", stats()))
        self.assertIn(
            "01 JAN 2027", chit.render_chit("light", stats(generated_on="2027-01-01"))
        )


class SharedSourceTests(unittest.TestCase):
    def test_the_signboard_strip_is_built_from_the_shared_stack(self):
        rendered = generate_kopi_sign.render_svg("light")
        for name, _ in generate_kopi_sign.STACK:
            self.assertIn(name, rendered)

    def test_every_tag_on_the_counter_is_one_the_signboard_claims(self):
        """The two cards must not disagree about what he works in."""
        claimed = {name for name, _ in generate_kopi_sign.STACK}
        for entry in chit.COUNTER:
            for tag in entry["stack"]:
                with self.subTest(entry=entry["name"], tag=tag):
                    self.assertIn(tag, claimed)


if __name__ == "__main__":
    unittest.main()
