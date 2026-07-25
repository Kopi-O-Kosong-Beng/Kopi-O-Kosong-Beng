from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_kopi_sign  # noqa: E402

ASSET_PATHS = {
    "dark": ROOT / "assets" / "kopi-sign-dark.svg",
    "light": ROOT / "assets" / "kopi-sign-light.svg",
}

REQUIRED_TEXT = (
    "KOPI O",
    "KOSONG BENG",
    "OPEN DAILY",
    "SINGAPORE",
    "咖啡乌",
    "无糖",
    "冰",
    "chia zhi feng",
    "谢梓峰",
)


class SignboardAssetTests(unittest.TestCase):
    def test_both_assets_exist_and_are_pure_ascii(self):
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                self.assertTrue(path.exists(), f"Missing {path}")
                source = path.read_text(encoding="utf-8")
                self.assertTrue(
                    source.startswith('<?xml version="1.0" encoding="UTF-8"?>\n')
                )
                self.assertTrue(source.isascii(), "SVG must be ASCII only")
                # read_text() applies universal newline translation, which would
                # silently accept a CRLF checkout; check the raw bytes instead.
                self.assertNotIn(b"\r\n", path.read_bytes())

    def test_assets_match_the_generator_exactly(self):
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                self.assertEqual(
                    path.read_text(encoding="utf-8"),
                    generate_kopi_sign.render_svg(theme),
                    "Asset has drifted from the generator. Re-run the script.",
                )

    def test_assets_share_geometry_and_accessibility_contract(self):
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                source = path.read_text(encoding="utf-8")
                root = ET.fromstring(source)
                self.assertEqual(root.attrib.get("viewBox"), "0 0 900 280")
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
                # A bare "//" check would false-positive on the xmlns
                # declaration's "http://www.w3.org/2000/svg", so guard the
                # protocol-relative form specifically instead.
                self.assertNotIn('src="//', source)
                self.assertNotIn('href="//', source)

    def test_assets_carry_the_signboard_copy(self):
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                root = ET.fromstring(path.read_text(encoding="utf-8"))
                rendered = "".join(root.itertext())
                for label in REQUIRED_TEXT:
                    self.assertIn(label, rendered)

    def test_the_drink_is_iced_and_never_steaming(self):
        for theme, path in ASSET_PATHS.items():
            with self.subTest(theme=theme):
                source = path.read_text(encoding="utf-8")
                self.assertIn("class=\"ice\"", source)
                self.assertIn("drop motion", source)
                self.assertNotIn("steam", source.lower())

    def test_the_two_variants_differ_only_in_colour(self):
        light = ASSET_PATHS["light"].read_text(encoding="utf-8")
        dark = ASSET_PATHS["dark"].read_text(encoding="utf-8")
        self.assertNotEqual(light, dark)
        # This only catches a palette key that is defined but never referenced in the template; it does not verify the committed asset files.
        for theme in ("light", "dark"):
            for token in generate_kopi_sign.PALETTES[theme].values():
                self.assertIn(token, generate_kopi_sign.render_svg(theme))
        strip_light = light
        strip_dark = dark
        for key, value in generate_kopi_sign.PALETTES["light"].items():
            strip_light = strip_light.replace(value, f"${key}")
        for key, value in generate_kopi_sign.PALETTES["dark"].items():
            strip_dark = strip_dark.replace(value, f"${key}")
        self.assertEqual(strip_light, strip_dark)

    def test_the_signal_lab_is_gone_for_good(self):
        stale = (
            ROOT / "assets" / "signal-lab-dark.svg",
            ROOT / "assets" / "signal-lab-light.svg",
            ROOT / "scripts" / "generate_signal_assets.py",
        )
        for path in stale:
            with self.subTest(path=path.name):
                self.assertFalse(
                    path.exists(),
                    f"{path.name} was superseded by the kopi signboard and must not return.",
                )


if __name__ == "__main__":
    unittest.main()
