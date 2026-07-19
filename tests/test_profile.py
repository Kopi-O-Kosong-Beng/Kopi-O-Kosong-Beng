from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
ASSET_PATHS = {
    "dark": ROOT / "assets" / "signal-lab-dark.svg",
    "light": ROOT / "assets" / "signal-lab-light.svg",
}


class ProfileReadmeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = README_PATH.read_text(encoding="utf-8")

    def test_readme_uses_theme_aware_signal_lab_assets(self):
        self.assertIn("<picture>", self.readme)
        self.assertIn('media="(prefers-color-scheme: dark)"', self.readme)
        self.assertIn("./assets/signal-lab-dark.svg", self.readme)
        self.assertIn("./assets/signal-lab-light.svg", self.readme)
        self.assertIn('width="100%"', self.readme)

    def test_readme_uses_approved_identity_copy_and_links(self):
        expected_copy = (
            "I study Computer Science and Design at SUTD. I like building "
            "things that connect software to the physical world."
        )
        self.assertIn(expected_copy, self.readme)
        self.assertIn("https://zhifeng-portfolio.vercel.app/", self.readme)
        self.assertIn(
            "https://www.linkedin.com/in/zhi-feng-chia-a50266210/",
            self.readme,
        )
        self.assertIn("mailto:zhifeng010729@gmail.com", self.readme)

    def test_readme_uses_html_middle_dot_separators(self):
        self.assertEqual(self.readme.count("&middot;"), 2)
        self.assertNotIn("\u00c2\u00b7", self.readme)

    def test_readme_has_exactly_two_native_easter_eggs(self):
        self.assertEqual(self.readme.count("<details>"), 2)
        self.assertEqual(self.readme.count("</details>"), 2)
        self.assertIn("<summary>a little more about me</summary>", self.readme)
        self.assertIn("<summary>why the username?</summary>", self.readme)
        self.assertNotIn("brew --profile", self.readme)
        self.assertNotIn("<summary><code>", self.readme)
        self.assertIn("kopi o kosong", self.readme.lower())

    def test_profile_easter_egg_uses_neutral_elsewhere_field(self):
        profile_block = self.readme.split("```text", 1)[1].split("```", 1)[0]
        self.assertIn("elsewhere", profile_block)
        self.assertNotIn("serious", profile_block)

    def test_readme_does_not_restore_legacy_marketing_content(self):
        forbidden = (
            "survive real users",
            "I run engineering at",
            "S$71K",
            "Selected builds",
            "Tools I reach for",
            "Co-founder",
            "open to internships",
            "ChatGPT",
            "Codex",
            "\u2014",
        )
        for phrase in forbidden:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, self.readme)

    def test_svg_assets_follow_the_shared_contract(self):
        required_text = (
            "CHIA ZHI FENG",
            "\u8c22\u6893\u5cf0",
            "CODE \u00b7 CIRCUITS \u00b7 COFFEE",
            "AI / ML",
            "BACKEND",
            "ROBOTS",
            "FPGA",
            "01\u00b017\u2032N / 103\u00b051\u2032E",
            "SIGNAL ONLINE",
        )

        for theme, asset_path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                self.assertTrue(asset_path.exists(), f"Missing {asset_path}")
                source = asset_path.read_text(encoding="utf-8")
                self.assertTrue(
                    source.startswith('<?xml version="1.0" encoding="UTF-8"?>\n')
                )
                self.assertTrue(source.isascii())
                root = ET.fromstring(source)
                rendered_text = "".join(root.itertext())
                self.assertEqual(root.attrib.get("viewBox"), "0 0 900 300")
                self.assertEqual(root.attrib.get("role"), "img")
                self.assertIn("aria-labelledby", root.attrib)
                self.assertIn("<title", source)
                self.assertIn("<desc", source)
                self.assertIn("prefers-reduced-motion: reduce", source)
                self.assertIn("animation: none !important", source)
                self.assertNotIn("<script", source.lower())
                self.assertNotIn("<image", source.lower())
                self.assertLess(
                    source.index('<circle class="signal motion"'),
                    source.index('<g transform="translate(100 158)">'),
                )
                for label in required_text:
                    self.assertIn(label, rendered_text)


if __name__ == "__main__":
    unittest.main()
