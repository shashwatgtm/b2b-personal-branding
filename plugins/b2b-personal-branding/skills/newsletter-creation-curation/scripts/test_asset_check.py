#!/usr/bin/env python3
"""Tests for asset_check.py. Run: python3 test_asset_check.py (standard library only)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asset_check as ac  # noqa: E402

ISSUE = """# Delivery Notes, issue 7 (hypothetical)

## Editor's note
Three launches this fortnight, all about agents doing the work around the work.

### An agentic platform for software delivery
Source: Happiest Minds press release, Thursday, June 11, 2026. https://www.happiestminds.com/press-releases/happiest-minds-launches-relaibuild-an-agentic-ai-platform-to-transform-enterprise-software-delivery/
What happened: a platform and a lifecycle method for AI agents across software delivery.

### A service desk product moves toward US federal buyers
Source: Freshworks press release, August 6, 2026.
What happened: Freshservice reached FedRAMP "In Process" status. Our hypothetical survey of 40 readers asked about it.
"""

CARD_OK = "Delivery Notes, issue 7\nThree launches this fortnight."
CARD_DRIFT = "Delivery Notes, issue 7\nFour launches. 45 readers told us."


class AssetCheckTests(unittest.TestCase):
    def test_item_without_link(self):
        rep = ac.check(ISSUE, {})
        self.assertEqual(rep["items"], 2)
        self.assertEqual(rep["items_without_link"], ["A service desk product moves toward US federal buyers"])
        self.assertFalse(rep["pass"])

    def test_drift_in_derived_asset(self):
        rep = ac.check(ISSUE, {"card": CARD_DRIFT})
        drift_values = {d["value"] for d in rep["drift"]}
        self.assertIn("45", drift_values)
        labels = {c["label"] for c in rep["label_conflicts"]}
        self.assertIn("readers", labels)

    def test_matching_card_has_no_drift(self):
        rep = ac.check(ISSUE, {"card": CARD_OK})
        self.assertEqual(rep["drift"], [])

    def test_right_weekday_passes_and_wrong_fails(self):
        self.assertEqual(ac.check(ISSUE, {})["weekday_errors"], [])
        rep = ac.check(ISSUE.replace("Thursday, June 11", "Friday, June 11"), {})
        self.assertEqual(len(rep["weekday_errors"]), 1)
        self.assertIn("Thursday", rep["weekday_errors"][0]["problem"])

    def test_numbers_in_urls_are_ignored(self):
        nums = ac.numbers_in("See https://example.com/release-302770347.html for details.")
        self.assertEqual(nums, [])

    def test_dash_found(self):
        rep = ac.check(ISSUE + "\nOne more line \u2014 with a dash.\n", {})
        self.assertIn("issue", rep["dashes"])

    def test_clean_set_passes(self):
        fixed = ISSUE.replace("Source: Freshworks press release, August 6, 2026.",
                              "Source: Freshworks press release, August 6, 2026. https://www.freshworks.com/press-releases/")
        rep = ac.check(fixed, {"card": CARD_OK})
        self.assertTrue(rep["pass"], rep)

    def test_main_exit_codes(self):
        import tempfile
        paths = []
        try:
            for body in (ISSUE, CARD_DRIFT):
                with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
                    f.write(body)
                    paths.append(f.name)
            self.assertEqual(ac.main([paths[0], "--derived", paths[1]]), 1)
        finally:
            for p in paths:
                os.unlink(p)

    # Run 31C, Codex finding F002: an issue with 0 curated items does not pass, unless the user's format is a deep dive (--deep-dive)
    ZERO = "0 curated items found: each item must start with a '### ' heading"
    DEEP = ("# Delivery Notes, issue 8 (hypothetical)\n\n## Editor's note\nOne topic this fortnight, from our own rollout.\n\n"
            "## The deep dive\nWhat we changed in our review step, and why. Source: https://www.happiestminds.com/press-releases/\n")

    def test_zero_items_do_not_pass(self):
        for issue in ("", "   \n", "## Pick of the week\nNo link here, just text.\n"):
            rep = ac.check(issue, {})
            self.assertFalse(rep["pass"], repr(issue))
            self.assertIn(self.ZERO, rep.get("problems", []), repr(issue))

    def _main(self, body, *flags):
        import io
        import tempfile
        from contextlib import redirect_stdout
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(body)
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                code = ac.main([f.name, *flags])
        finally:
            os.unlink(f.name)
        return code, buf.getvalue()

    def test_main_zero_items_exit_1_with_message(self):
        code, out = self._main("## Pick of the week\nNo link here, just text.\n")
        self.assertEqual(code, 1)
        self.assertIn(self.ZERO, out)
        self.assertNotIn("PASS", out.splitlines()[-1])

    def test_deep_dive_flag_allows_zero_items(self):
        rep = ac.check(self.DEEP, {}, deep_dive=True)
        self.assertTrue(rep["pass"], rep)
        code, out = self._main(self.DEEP, "--deep-dive")
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines()[-1], "PASS")
        code, out = self._main(self.DEEP)
        self.assertEqual(code, 1, out)

    # Run 31C auditor gaps S-A to S-D: a heading inside a code fence is not an item; an item heading with no title is a problem;
    # a UTF-8 byte order mark does not hide the first item; a file that cannot be read is one line and exit 2, never a traceback
    def test_heading_inside_code_fence_is_not_an_item(self):
        rep = ac.check("## Deep\n```\n### Fake heading\nhttps://x.com\n```\n", {})
        self.assertEqual(rep["items"], 0)
        self.assertFalse(rep["pass"])

    def test_item_heading_with_no_title_is_a_problem(self):
        rep = ac.check("### \nhttps://x.com\n", {})
        self.assertFalse(rep["pass"])
        self.assertTrue(any("no title" in p for p in rep.get("problems", [])), rep)

    def test_byte_order_mark_does_not_hide_first_item(self):
        import tempfile
        with tempfile.NamedTemporaryFile("wb", suffix=".md", delete=False) as f:
            f.write(b"\xef\xbb\xbf### One item\nhttps://x.com/a\n")
        try:
            self.assertEqual(ac.read(f.name).count("### "), 1)
            self.assertTrue(ac.read(f.name).startswith("### "))
        finally:
            os.unlink(f.name)

    def test_missing_file_is_one_line_and_exit_2(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = ac.main([os.path.join(os.path.dirname(os.path.abspath(__file__)), "no-such-issue.md")])
        self.assertEqual(code, 2)
        self.assertIn("cannot read", buf.getvalue())

    def test_deep_dive_still_checks_items_and_empty_issue(self):
        rep = ac.check(ISSUE, {}, deep_dive=True)
        self.assertEqual(rep["items_without_link"], ["A service desk product moves toward US federal buyers"])
        self.assertFalse(rep["pass"])
        empty = ac.check("  \n", {}, deep_dive=True)
        self.assertFalse(empty["pass"])
        self.assertTrue(any("empty" in p for p in empty.get("problems", [])))


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

    def test_item_with_rupee_and_quotes(self):
        p = _run_cp1252("asset_check.py", ["{0}"], [("issue.md", "# Issue\n\n### \u201cItem one\u201d \u20b951.4 crore\nhttps://example.org/a\nRevenue \u20b951.4 crore, \u221214%.\n")])
        self.assert_utf8_output(p, "\u20b9")

    def test_json(self):
        p = _run_cp1252("asset_check.py", ["{0}", "--json"], [("issue.md", "# Issue\n\n### \u201cItem one\u201d \u20b951.4 crore\nhttps://example.org/a\n")])
        self.assertNotIn(b"Traceback", p.stderr, p.stderr.decode("utf-8", "replace"))
        self.assertIn(p.returncode, (0, 1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
