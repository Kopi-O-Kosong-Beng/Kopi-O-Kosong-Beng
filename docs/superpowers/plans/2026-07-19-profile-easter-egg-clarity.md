# Profile Easter Egg Clarity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the optional README sections look clearly clickable instead of resembling commands that visitors must run.

**Architecture:** Keep the existing GitHub native `details` elements and all immediately visible profile content. Change only the two summary labels and strengthen the existing README contract test so the command presentation cannot return.

**Tech Stack:** GitHub Flavored Markdown, HTML `details` elements, Python `unittest`

## Global Constraints

The animated signal lab, introduction, portfolio link, LinkedIn link, and email link must remain visible immediately.

The README must retain exactly two native expandable sections.

The text `brew --profile` and code styled summary labels must be absent.

No ChatGPT or Codex co author trailer may be added to any commit.

---

### Task 1: Clarify the expandable profile labels

**Files:**

- Modify: `tests/test_profile.py:43`
- Modify: `README.md:19`

**Interfaces:**

- Consumes: The existing README string loaded by `ProfileReadmeTests.setUpClass`.
- Produces: Two native expandable sections with plain summary labels and a regression test for their exact presentation.

- [ ] **Step 1: Write the failing test**

Replace `test_readme_has_exactly_two_native_easter_eggs` with:

```python
def test_readme_has_exactly_two_native_easter_eggs(self):
    self.assertEqual(self.readme.count("<details>"), 2)
    self.assertEqual(self.readme.count("</details>"), 2)
    self.assertIn("<summary>a little more about me</summary>", self.readme)
    self.assertIn("<summary>why the username?</summary>", self.readme)
    self.assertNotIn("brew --profile", self.readme)
    self.assertNotIn("<summary><code>", self.readme)
    self.assertIn("kopi o kosong", self.readme.lower())
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```powershell
python -m unittest -v tests.test_profile.ProfileReadmeTests.test_readme_has_exactly_two_native_easter_eggs
```

Expected: `FAIL` because the README still contains `brew --profile` and code styled summaries.

- [ ] **Step 3: Apply the minimal README change**

Replace the two summary lines with:

```html
<summary>a little more about me</summary>
```

and:

```html
<summary>why the username?</summary>
```

Do not alter the animation, visible introduction, links, or expandable section contents.

- [ ] **Step 4: Run the complete validation suite**

Run:

```powershell
python -m unittest -v tests/test_profile.py
python -c "import xml.etree.ElementTree as ET; ET.parse('assets/signal-lab-dark.svg'); ET.parse('assets/signal-lab-light.svg'); print('SVG XML valid')"
git diff --check
```

Expected: All seven tests pass, the SVG command prints `SVG XML valid`, and `git diff --check` produces no errors.

- [ ] **Step 5: Commit and push the verified change**

Run:

```powershell
git add -- README.md tests/test_profile.py
git commit -m "fix: clarify profile easter eggs"
git push origin main
```

Expected: The commit lists only Zhi Feng as author and committer, and `origin/main` advances to the new commit.
