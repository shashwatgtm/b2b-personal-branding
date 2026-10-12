#!/usr/bin/env python3
"""Tests for voice_scan.py. Run: python3 test_voice_scan.py (standard library only)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voice_scan as vs  # noqa: E402

BAD = (
    "Humbled to share that our launch is a game-changer \u2014 and it was seamless!\n"
    "That's not a feature. That's a movement.\n"
    "Big news. Huge win.\n"
    "First, we listened.\n"
    "Second, we shipped.\n"
    "Start on Monday and move the needle with this rubric \U0001F680.\n"
    "\U0001D5D5\U0001D5FC\U0001D5F9\U0001D5F1 claims \u2192 proof \u2705\n"
    "I'm a thought leader in agentic CX.\n"
    "We go live on Thursday, 13 May 2026.\n"
    "Text with a broken quote \u00e2\u20ac\u2122 here.\n"
    "Why would anyone wait?\n"
    "What would you change in your own team?\n"
)

CLEAN = (
    "I spent three weeks listening to support calls before we wrote a line of copy.\n"
    "The pattern surprised me: agents wanted help after the call, not during it.\n"
    "We rebuilt the launch story around that, and the first customer demo ran long because "
    "the floor manager kept asking about after-call summaries.\n"
    "What do your agents ask for first?\n"
)


def kinds(res):
    return [f["kind"] for f in res["flags"]]


class VoiceScanTests(unittest.TestCase):
    def test_bad_text_fires_every_detector(self):
        res = vs.scan(BAD)
        k = kinds(res)
        for expected in ["dash", "banned word", "exclamation", "not X, Y", "fragment", "enumeration",
                         "lazy line", "emoji", "unicode bold", "arrow", "checkmark", "self label",
                         "date", "encoding", "question"]:
            self.assertIn(expected, k, f"missing detector: {expected}")
        spans = " ".join(f["span"].lower() for f in res["flags"])
        for word in ["game-changer", "seamless", "move the needle", "rubric", "humbled to share"]:
            self.assertIn(word, spans)

    def test_wrong_weekday_found_and_named(self):
        res = vs.scan("Launch on Thursday, 13 May 2026.")
        d = [f for f in res["flags"] if f["kind"] == "date"]
        self.assertEqual(len(d), 1)
        self.assertIn("Wednesday", d[0]["rule"])

    def test_right_weekday_passes(self):
        res = vs.scan("Launch on Wednesday, May 13, 2026, as planned.")
        self.assertNotIn("date", kinds(res))

    def test_clean_text_has_no_banned_flags(self):
        res = vs.scan(CLEAN)
        self.assertEqual(res["stats"]["banned_flags"], 0, res["flags"])
        # the closing open question is allowed
        self.assertNotIn("question", kinds(res))

    def test_hyphen_inside_word_and_list_marker_are_not_dashes(self):
        res = vs.scan("- after-call work is a well-known pain\n- second item\n")
        self.assertNotIn("dash", kinds(res))

    def test_spaced_hyphen_is_a_dash(self):
        res = vs.scan("We shipped it - and then we waited.")
        self.assertIn("dash", kinds(res))

    def test_skip_quotes_leaves_source_wording(self):
        line = 'The release says the core "integrates seamlessly with existing enterprise ecosystems." We tested it.'
        self.assertIn("banned word", kinds(vs.scan(line)))
        self.assertNotIn("banned word", kinds(vs.scan(line, skip_quotes=True)))

    def test_curly_apostrophes_still_match(self):
        res = vs.scan("In today’s world, here’s the thing: it’s important to note this.")
        spans = " ".join(f["span"].lower() for f in res["flags"] if f["kind"] == "banned word")
        for phrase in ["in today’s world", "here’s the thing", "it’s important to note"]:
            self.assertIn(phrase, spans)

    def test_url_is_not_prose(self):
        res = vs.scan("Source: https://example.com/a--b!c")
        self.assertNotIn("dash", kinds(res))
        self.assertNotIn("exclamation", kinds(res))

    def test_landscape_is_review_not_banned(self):
        res = vs.scan("The competitive landscape changed in one quarter for us.")
        sev = {f["kind"]: f["severity"] for f in res["flags"]}
        self.assertEqual(sev.get("review word"), "review")
        self.assertEqual(res["stats"]["banned_flags"], 0)

    def test_reading_grade_is_reported(self):
        res = vs.scan(CLEAN)
        self.assertIsNotNone(res["stats"]["approx_reading_grade"])
        self.assertIn(res["stats"]["approx_band"], ["secondary school", "upper secondary", "graduate", "above graduate"])

    def test_strict_exit_code(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(BAD)
            path = f.name
        try:
            self.assertEqual(vs.main([path, "--strict"]), 1)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
