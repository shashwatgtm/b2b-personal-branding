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


if __name__ == "__main__":
    unittest.main(verbosity=2)
