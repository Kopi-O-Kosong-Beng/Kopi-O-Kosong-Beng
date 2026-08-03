from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
README_EN = ROOT / "README.md"
README_ZH = ROOT / "README.zh.md"

BANNED_WIDGETS = (
    "shields.io",
    "skillicons",
    "readme-typing-svg",
    "github-readme-stats",
    "streak-stats",
    "github-profile-trophy",
    "contribution-graph",
    "contribution-snake",
    "snk.svg",
)

# Covers both languages: English phrases first, Chinese terms after.
BANNED_JOB_SEEKING = (
    "seeking",
    "open to opportunit",
    "available for",
    "looking for a role",
    "internship",
    "hire me",
    "求职",
    "实习",
    "找工作",
    "招聘",
    "应聘",
    "内推",
    "求一份",
)

BANNED_METRICS = (
    "S$71K",
    "71K",
    "237",
    "87.5",
    "34%",
    "16%",
    "51%",
    "4.57",
    "18,000",
)

BANNED_VOCAB = (
    "passionate",
    "leverage",
    "seamless",
    "robust",
    "cutting edge",
    "journey",
    "showcase",
    "delve",
    "dive into",
    "tapestry",
    "realm",
    "landscape",
    "testament",
    "elevate",
    "unlock",
    "empower",
    "foster",
    "dedicated",
    "driven",
    "enthusiast",
)

LINKS = (
    "https://zhifeng-portfolio.vercel.app/",
    "https://www.pitchmesg.com",
    "https://www.linkedin.com/in/zhi-feng-chia-a50266210/",
    "mailto:zhifeng010729@gmail.com",
)

# UTF-8 bytes misread as cp1252
MOJIBAKE = (
    'Â·',
    'â€”',
    'ï¿½',
)


class ProfileCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.english = README_EN.read_text(encoding="utf-8")
        cls.chinese = README_ZH.read_text(encoding="utf-8")

    @staticmethod
    def prose_only(text):
        """Strip link targets and HTML attribute values.

        The digit scan must read prose, not addresses. Without this the email
        zhifeng010729@gmail.com and the LinkedIn slug a50266210 both look like
        stray metrics.
        """
        stripped = re.sub(r"\]\([^)]*\)", "]", text)
        return re.sub(r'[\w-]+="[^"]*"', "", stripped)

    def assert_shared_contract(self, text, label):
        """Checks run against both language files.

        Most of these are genuinely language neutral: they test structure
        (signboard markup, alt text presence, easter egg count), or literal
        strings/characters that are not translated prose (widget domains,
        banned metrics, dash characters, digits, links, mojibake byte
        sequences, retired signal-lab branding), so they catch real problems
        in either file. BANNED_JOB_SEEKING also covers both languages: English
        phrases and Chinese terms. BANNED_VOCAB remains English only by
        design, it is a lexical filter on English filler words and does not
        check Chinese phrasing, so do not assume it guards README.zh.md.
        """
        with self.subTest(check="theme aware signboard", file=label):
            self.assertIn("<picture>", text)
            self.assertIn('media="(prefers-color-scheme: dark)"', text)
            self.assertIn('media="(prefers-color-scheme: light)"', text)
            self.assertIn("./assets/kopi-sign-dark.svg", text)
            self.assertIn("./assets/kopi-sign-light.svg", text)
            self.assertIn('width="100%"', text)
            self.assertIn('src="./assets/kopi-sign-light.svg"', text)

        with self.subTest(check="theme aware order chit", file=label):
            self.assertIn("./assets/kopi-chit-dark.svg", text)
            self.assertIn("./assets/kopi-chit-light.svg", text)
            self.assertIn('src="./assets/kopi-chit-light.svg"', text)

        with self.subTest(check="both cards have alt text", file=label):
            self.assertEqual(text.count("<picture>"), 2)
            self.assertEqual(text.count("</picture>"), 2)
            self.assertEqual(len(re.findall(r'<img alt="[^"]{20,}"', text)), 2)

        with self.subTest(check="cards are local, never remote", file=label):
            # The whole point of generating these is that no third party serves
            # them. A remote card would be a slop widget wearing our palette.
            for asset in re.findall(r'(?:srcset|src)="([^"]*kopi-[^"]*)"', text):
                self.assertTrue(
                    asset.startswith("./assets/"), f"{asset} is not a local asset"
                )

        with self.subTest(check="only the diving depth", file=label):
            numbers = set(re.findall(r"\d+", self.prose_only(text)))
            self.assertTrue(
                numbers <= {"18"},
                f"Unexpected numbers in {label}: {sorted(numbers - {'18'})}",
            )

        with self.subTest(check="no slop widgets", file=label):
            for widget in BANNED_WIDGETS:
                self.assertNotIn(widget, text.lower())

        with self.subTest(check="no job seeking", file=label):
            for phrase in BANNED_JOB_SEEKING:
                self.assertNotIn(phrase, text.lower())

        with self.subTest(check="no metrics", file=label):
            for metric in BANNED_METRICS:
                self.assertNotIn(metric, text)

        with self.subTest(check="no dashes as punctuation", file=label):
            # U+2014 EM DASH, U+2013 EN DASH, U+2015 HORIZONTAL BAR, U+FF0D FULLWIDTH HYPHEN MINUS
            banned_dashes = ("—", "–", "―", "－")
            for dash in banned_dashes:
                self.assertNotIn(
                    dash,
                    text,
                    f"{label} contains banned dash character U+{ord(dash):04X}",
                )

        with self.subTest(check="no banned vocabulary", file=label):
            for entry in BANNED_VOCAB:
                pattern = r"(?<![A-Za-z])" + re.escape(entry) + r"(?![A-Za-z])"
                self.assertIsNone(
                    re.search(pattern, text, flags=re.IGNORECASE),
                    f"{label} contains banned wording: {entry}",
                )

        with self.subTest(check="links present", file=label):
            for link in LINKS:
                self.assertIn(link, text)

        with self.subTest(check="exactly two easter eggs", file=label):
            self.assertEqual(text.count("<details>"), 2)
            self.assertEqual(text.count("</details>"), 2)

        with self.subTest(check="no mojibake", file=label):
            for garbled in MOJIBAKE:
                self.assertNotIn(garbled, text)

        with self.subTest(check="signal lab is gone for good", file=label):
            for phrase in ("signal-lab", "SIGNAL LAB", "CODE · CIRCUITS · COFFEE"):
                self.assertNotIn(phrase, text)

    def test_english_readme_meets_the_shared_contract(self):
        self.assert_shared_contract(self.english, "README.md")

    def test_english_readme_carries_the_menu_sections(self):
        for heading in ("NOW SERVING", "ON THE SIDE", "ALSO IN THE CUP"):
            self.assertIn(heading, self.english)

    def test_english_readme_leads_with_pitchme(self):
        serving = self.english.index("NOW SERVING")
        side = self.english.index("ON THE SIDE")
        self.assertIn("pitchMe", self.english[serving:side])
        self.assertIn("co-founder and CTO", self.english[serving:side])

    def test_english_readme_closes_with_the_signature(self):
        self.assertTrue(
            self.english.rstrip().endswith(
                '<p align="center"><i>no sugar. never was.</i></p>'
            )
        )

    def test_chinese_readme_meets_the_shared_contract(self):
        self.assert_shared_contract(self.chinese, "README.zh.md")

    def test_chinese_readme_carries_the_menu_sections(self):
        for heading in ("今日供应", "配菜", "杯里还有"):
            self.assertIn(heading, self.chinese)
        self.assertIn("pitchMe", self.chinese)
        self.assertTrue(
            self.chinese.rstrip().endswith(
                '<p align="center"><i>不要糖。从来都不要。</i></p>'
            )
        )

    def test_the_language_switch_works_in_both_directions(self):
        self.assertIn('href="./README.zh.md"', self.english)
        self.assertIn(">中文</a>", self.english)
        self.assertIn('href="./README.md"', self.chinese)
        self.assertIn(">English</a>", self.chinese)


if __name__ == "__main__":
    unittest.main()
