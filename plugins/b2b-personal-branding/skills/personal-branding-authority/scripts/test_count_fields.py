#!/usr/bin/env python3
"""Tests for count_fields.py. Run: python3 test_count_fields.py (standard library only)."""
import os
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

    def test_main_runs(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(ASSETS)
            path = f.name
        try:
            self.assertEqual(cf.main([path, "--limit", "Headline=220"]), 0)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
