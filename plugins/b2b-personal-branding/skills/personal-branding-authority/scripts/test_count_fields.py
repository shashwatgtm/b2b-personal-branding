#!/usr/bin/env python3
"""Tests for count_fields.py. Run: python3 test_count_fields.py (standard library only)."""
import os
import subprocess
import tempfile
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import count_fields as cf  # noqa: E402

ASSETS = """## Headline
Product marketing lead for IT service management software | 12 years in B2B SaaS

## Short bio
[Name] leads product marketing for an IT service management product. Over 14 years in B2B SaaS, [Name] has launched 6 products.

## Medium bio
[Name] has spent 12 years in B2B SaaS marketing \u2014 most of it close to IT teams. Speaking on Thursday, 13 May 2026.
"""


class CountFieldsTests(unittest.TestCase):
    def test_counts_each_field(self):
        rep = cf.check(ASSETS)
        names = [f["field"] for f in rep["fields"]]
        self.assertEqual(names, ["Headline", "Short bio", "Medium bio"])
        head = rep["fields"][0]
        body = "Product marketing lead for IT service management software | 12 years in B2B SaaS"
        self.assertEqual(head["characters"], len(body))
        self.assertEqual(head["words"], len(body.split()))

    def test_label_conflict_found(self):
        rep = cf.check(ASSETS)
        labels = {c["label"]: c["values"] for c in rep["label_conflicts"]}
        self.assertIn("years", labels)
        self.assertEqual(set(labels["years"].keys()), {"12", "14"})

    def test_dash_found(self):
        rep = cf.check(ASSETS)
        self.assertTrue(rep["fields"][2]["dashes"])
        self.assertFalse(rep["fields"][0]["dashes"])

    def test_weekday_error(self):
        rep = cf.check(ASSETS)
        self.assertEqual(len(rep["weekday_errors"]), 1)
        self.assertIn("Wednesday", rep["weekday_errors"][0]["problem"])

    def test_limit_over_and_within(self):
        rep = cf.check(ASSETS, {"Headline": 40, "Short bio": 500})
        self.assertGreater(rep["fields"][0]["over_limit_by"], 0)
        self.assertEqual(rep["fields"][1]["over_limit_by"], 0)

    def test_consistent_numbers_pass(self):
        rep = cf.check("## A\n12 years here\n## B\nstill 12 years there\n")
        self.assertEqual(rep["label_conflicts"], [])

    def test_no_headings_is_one_field(self):
        rep = cf.check("Just one block of text with 3 launches.")
        self.assertEqual(len(rep["fields"]), 1)
        self.assertIn("3 launches", rep["fields"][0]["numbers"])

    def test_draft_labels_not_counted(self):
        body = "[Name] runs a monthly roundtable for retail loyalty heads. [Draft for you to confirm: the roundtable is for the buyers the company page names] [User to add: years in the role]"
        rep = cf.check("## Website bio\n" + body + "\n")
        f = rep["fields"][0]
        self.assertEqual(f["words"], len(body.split()))
        self.assertEqual(f["final_words"], len(body.split()) - 5)
        self.assertEqual(f["draft_labels"], 1)
        self.assertEqual(f["placeholders_open"], 1)
        self.assertNotIn("Draft for you to confirm", cf.without_labels(body))
        self.assertIn("the roundtable is for the buyers the company page names", cf.without_labels(body))

    def test_principal_marker_not_counted(self):
        rep = cf.check("## Bio\nShe leads the team. [Principal to confirm]\n")
        self.assertEqual(rep["fields"][0]["final_words"], 4)

    def test_limit_uses_count_without_labels(self):
        body = "[Draft for you to confirm: tenletters]"
        rep = cf.check("## Headline\n" + body + "\n", {"Headline": 10})
        self.assertEqual(rep["fields"][0]["final_characters"], 10)
        self.assertEqual(rep["fields"][0]["over_limit_by"], 0)

    def test_no_labels_counts_equal(self):
        rep = cf.check(ASSETS)
        for f in rep["fields"]:
            self.assertEqual(f["final_words"], f["words"])
            self.assertEqual(f["final_characters"], f["characters"])

    def test_draft_line_holding_name_placeholder(self):
        draft = "[Name] works with heads of loyalty at retail brands, the buyers the company's own About page names."
        body = ("[Name] runs the loyalty programme team for a retail brand and spends one week each quarter on store floors "
                "with the cashiers who enrol members. [Draft for you to confirm: " + draft + "] "
                "[Name] has led the team for [User to add: years].")
        rep = cf.check("## Website bio\n" + body + "\n", {"Website bio": 300})
        f = rep["fields"][0]
        self.assertEqual(f["draft_labels"], 1)
        self.assertEqual(f["final_words"], len(body.split()) - 5)
        self.assertEqual(f["placeholders_open"], 1)
        self.assertIn(draft, cf.without_labels(body))
        self.assertEqual(f["over_limit_by"], max(0, len(cf.without_labels(body)) - 300))

    def test_main_runs(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(ASSETS)
            path = f.name
        try:
            self.assertEqual(cf.main([path, "--limit", "Headline=220"]), 0)
        finally:
            os.unlink(path)


def _run_cp1252(script_name, args, files):
    """S2, run 32A: run the script as a user on Windows would, with output set to code page 1252 (a console or pipe)."""
    import subprocess
    import tempfile
    d = tempfile.mkdtemp()
    paths = []
    for name, body in files:
        p = os.path.join(d, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(body)
        paths.append(p)
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    env = dict(os.environ, PYTHONIOENCODING="cp1252")
    return subprocess.run([sys.executable, script] + [a.format(*paths) for a in args], capture_output=True, env=env)


class CodePage1252Tests(unittest.TestCase):
    """S2, run 32A: a character outside plain ASCII (rupee sign, Unicode minus, curly quotes) is written as UTF-8 and the
    script never stops with an encoding error on a Windows console or pipe set to code page 1252."""

    def assert_utf8_output(self, p, expected):
        self.assertNotIn(b"Traceback", p.stderr, p.stderr.decode("utf-8", "replace"))
        self.assertNotIn(b"UnicodeEncodeError", p.stderr)
        self.assertIn(p.returncode, (0, 1))
        self.assertIn(expected.encode("utf-8"), p.stdout)

    def test_field_with_rupee_and_quotes(self):
        p = _run_cp1252("count_fields.py", ["{0}"], [("f.txt", "## Headline \u20b9 \u201cAlpha\u201d\nRevenue \u20b951.4 crore \u221214%.\n")])
        self.assert_utf8_output(p, "\u20b9")

    def test_json(self):
        p = _run_cp1252("count_fields.py", ["{0}", "--json"], [("f.txt", "## Headline \u20b9 \u201cAlpha\u201d\nRevenue \u20b951.4 crore \u221214%.\n")])
        self.assert_utf8_output(p, "\u20b9")


class BadLimitTests(unittest.TestCase):
    """Run 33A (judge 33A-2, PBL-1): --limit "Short bio=50w" ended in a ValueError traceback. A limit that is not a whole
    number of characters is bad input with a plain message and exit code 2, never a traceback; a good limit still works."""

    def run_script(self, *args):
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "count_fields.py")
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "assets.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("## Short bio\nOne two three four five.\n")
            return subprocess.run([sys.executable, "-I", script, path, *args], capture_output=True, text=True)

    def test_bad_limit_values(self):
        for value in ("Short bio=50w", "Short bio=fifty", "Short bio=", "Short bio=-5", "Short bio=12.5", "Short bio"):
            p = self.run_script("--limit", value)
            self.assertNotIn("Traceback", p.stderr, (value, p.stderr))
            self.assertEqual(p.returncode, 2, (value, p.returncode, p.stdout, p.stderr))
            self.assertIn("bad --limit", p.stdout + p.stderr, value)

    def test_non_ascii_digits_refused(self):
        """Auditor gaps 1 and 2: superscript, circled and Arabic-Indic digits are not a whole number of characters."""
        for value in ("Short bio=\u00b2", "Short bio=\u2460", "Short bio=\u0663"):
            p = self.run_script("--limit", value)
            self.assertNotIn("Traceback", p.stderr, (value, p.stderr))
            self.assertEqual(p.returncode, 2, (value, p.returncode, p.stdout))

    def test_limit_for_a_field_not_in_the_file_refused(self):
        """Auditor gap 3: a limit whose field is not a "## " heading in the file (a typo) is bad input, never a silent pass."""
        p = self.run_script("--limit", "Short bios=50")
        self.assertEqual(p.returncode, 2, (p.returncode, p.stdout))
        self.assertIn("no field", p.stdout)

    def test_huge_limit_refused(self):
        """Re-check of round 2: a limit of thousands of digits ended in a ValueError traceback (int() refuses over 4,300 digits)."""
        p = self.run_script("--limit", "Short bio=" + "9" * 5000)
        self.assertNotIn("Traceback", p.stderr)
        self.assertEqual(p.returncode, 2, (p.returncode, p.stdout[:200]))

    def test_good_limit_still_works(self):
        p = self.run_script("--limit", "Short bio=50")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("limit 50, within limit", p.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
