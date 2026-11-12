# Voice scan: the method

This file sets out one fixed check: the voice scan of a text written for a reader. It finds dashes, banned words and phrases, review words, banned patterns, exclamation marks, short fragments, rhetorical questions, emoji, Unicode bold, arrows, checkmarks, broken encoding and wrong weekdays next to dates, line by line, and reports counts and an approximate reading grade. Follow the rules exactly. When code execution is available, write your own calculation from these rules and run it; otherwise work it out by hand and say "counted by hand per the method". Either way the printed lines must match the shapes below character for character.

The patterns below are written as Python regular expressions (the `re` module, with its default Unicode behaviour: `\w` is any Unicode letter, digit or underscore, `\s` is any Unicode white space, `\d` is any Unicode decimal digit, `\b` is a word boundary). A code implementation should use them as written. By hand, read each pattern by its plain English gloss.

Nothing here is a benchmark. The banned list is the same list as references/banned-words-and-patterns.md, section 1; when the user has their own list, theirs is added by reading, after the scan.

## Inputs

| Input | Required | Meaning |
|---|---|---|
| text | yes | The text to scan. When it comes from a file, read the file as UTF-8, replace any byte that is not valid UTF-8 with U+FFFD, and turn every CR LF pair and every lone CR into LF. A byte order mark at the start is kept as the character U+FEFF. |
| skip_quotes | no (default off) | On when the text quotes a source: text inside double quotes is left alone (see Masks). |
| format | no (default text) | text or json. |
| strict | no (default off) | On: the check fails (exit status 1) when there is at least one banned flag. It changes nothing in the printed output. |

## Lines and masks

**Lines.** Split the text into lines the way Python `str.splitlines()` does: at LF, and also at U+000B, U+000C, U+001C, U+001D, U+001E, U+0085, U+2028 and U+2029. Lines are numbered from 1. A final line break does not start a new line.

**URL mask.** Every match of `https?://\S+|www\.\S+` (a web address up to the next white space) is replaced by the same number of spaces. Each character becomes one space, so positions do not move.

**Quote mask** (only when skip_quotes is on). Every match of `"[^"]*"|\u201c[^\u201d]*\u201d` (a straight double quote to the next straight double quote, or a left curly double quote U+201C to the next right curly double quote U+201D, quote marks included) is replaced by the same number of spaces. Single quotes are never masked. Applied to one line, a quote cannot reach past the line; applied to the whole text (in Part B and in the reading grade), a straight quote pair can span several lines.

**The scan line.** For each line: apply the quote mask (only when skip_quotes is on), then the URL mask. Call the result the scan line and the original the raw line. They have the same length.

**The lowered line.** The scan line in lower case (Python `str.lower()`), then every U+2019 and every U+2018 replaced by a straight apostrophe ('). Used only for the banned and review lists.

**Spans.** Where a rule says "span from the raw line, from position a to b", take the characters of the raw line at those positions, using the positions found in the scan line or lowered line. A start below 0 is 0; an end past the line is the end of the line. "Trimmed" means white space removed from both ends (Python `str.strip()`).

## The lists

**Banned words and phrases** (severity banned), in this exact order:

game-changer, game changer, game-changing, game changing, leverage, leveraging, leveraged, dive in, dive into, dive deep, delve, delves, delving, tapestry, elevate, elevated, elevates, unlock, unlocks, unlocking, seamless, seamlessly, landed hard, resonated, resonates, struck a chord, genuine unlock, genuinely, honestly, straightforward, revolutionize, revolutionise, supercharge, harness, empower, empowers, in today's world, in the ever-evolving landscape, ever-evolving, to the next level, it's important to note, testament to, the rise of, keep coming back to, sat with me, rubric, move the needle, here's the thing, groundbreaking, revolutionary, transformative, comprehensive, robust, holistic, synergy, synergies, paradigm shift, next-level, next level, humbled to share, humbled and honored, thrilled to announce, thrilled to share, excited to announce, excited to share

(The apostrophes in "in today's world", "it's important to note" and "here's the thing" are straight apostrophes, U+0027. The hyphens are the keyboard hyphen, U+002D.)

**Review words** (severity review), in this exact order, each with its rule text:

| Word | Rule text |
|---|---|
| landscape | allowed only as a domain modifier, for example 'competitive landscape' |
| navigate | banned for abstract things; fine for a literal route |
| navigating | banned for abstract things; fine for a literal route |
| dynamic | banned as praise; fine as a technical term such as 'dynamic pricing' |
| mechanics | banned as a vague label; fine when literal |
| just | banned as filler; keep only when it carries meaning |
| thought leader | never applied to oneself |
| thought leadership | never applied to oneself |
| incredible | hyperbole |
| unprecedented | hyperbole |
| massive | hyperbole |
| mind-blowing | hyperbole |

A list entry matches in the lowered line wherever it appears with no word character and no hyphen directly before it and none directly after it: the pattern is `(?<![\w-])` + the entry (every character literal) + `(?![\w-])`. So "leverage" does not match inside "leveraged" or "leverage-free", and "thought leader" does not match inside "thought leadership". Overlapping entries each match on their own: "to the next level" also gives "next level".

## Part A. Rules applied line by line

For each line, in line order, add flags in exactly this order. A flag has: line, kind, severity, span, rule.

1. **Dash** (kind `dash`, banned, rule `no long, short or spaced dashes`). Every match in the scan line of `[\u2012\u2013\u2014\u2015]|(?<=\s)-(?=\s)|(?<=\w)--(?=\w)|\s--\s`: a figure dash, en dash, em dash or horizontal bar; a single hyphen with white space directly on both sides; two hyphens between two word characters; or two hyphens with white space on both sides (the white space is part of the match). Skip a match that is a single hyphen standing at the first position after the scan line's leading white space (a list marker such as "- item"). Leading white space is counted on the scan line, so with skip_quotes on, a hyphen right after a masked quote at the start of a line counts as leading and is skipped. Span: raw line from (match start minus 15) to (match end plus 15), trimmed.
2. **Banned word** (kind `banned word`, banned). For each banned entry in list order, every match in the lowered line, left to right. Span: raw line from match start to match end. Rule: `banned word or phrase: ` + the entry.
3. **Review word** (kind `review word`, review). For each review word in list order, every match in the lowered line. Span: raw line from match start to match end. Rule: the rule text from the table.
4. **Self label** (kind `self label`, banned, rule `'thought leader' applied to oneself`). At most one per line: the first match in the scan line, ignoring case, of `\b(?:I am|I'm|I\u2019m|as a|me as a|position me as a?)\s+(?:an?\s+)?thought leader`. Span: the matched text itself.
5. **Exclamation** (kind `exclamation`, banned, rule `no exclamation marks in published text`). Every "!" in the scan line. Span: raw line from (position minus 20) to (position plus 1), trimmed.
6. **Emoji** (kind `emoji`, banned, rule `no emoji`). Every match of `(?:(?![\u2713\u2714\u2705\u274c\u2611\u2612\u27a1])[\U0001F300-\U0001FAFF\U0001F000-\U0001F2FF\u2600-\u26ff\u2700-\u27bf])+\ufe0f?`: one or more characters from U+1F300 to U+1FAFF, U+1F000 to U+1F2FF, U+2600 to U+26FF or U+2700 to U+27BF, none of them U+2713, U+2714, U+2705, U+274C, U+2611, U+2612 or U+27A1, then an optional U+FE0F. A run of emoji is one match. Span: raw line from (match start minus 10) to (match end plus 10), trimmed.
7. **Unicode bold** (kind `unicode bold`, banned, rule `no Unicode bold or italic letters`). Every run matching `[\U0001D400-\U0001D7FF]+`. Span as for emoji.
8. **Arrow** (kind `arrow`, banned, rule `no arrows in prose`). Every match of `[\u2190-\u21ff\u27a1\u2b05-\u2b0d]|(?<!\w)(?:->|=>)(?!\w)`: an arrow character (U+2190 to U+21FF, U+27A1, U+2B05 to U+2B0D), or "->" or "=>" with no word character directly before or after. So "x->y" is not flagged. Span as for emoji.
9. **Checkmark** (kind `checkmark`, banned, rule `no checkmarks or cross marks`). Every U+2713, U+2714, U+2705, U+274C, U+2611 or U+2612, one flag each. Span as for emoji.
10. **Encoding** (kind `encoding`, banned, rule `broken character encoding; ask for a clean copy`). Every match of `\ufffd|\u00e2\u20ac|\u00c3[\u0080-\u00bf]`: the replacement character, the pair U+00E2 U+20AC, or U+00C3 followed by a character from U+0080 to U+00BF. Span as for emoji.
11. **Lazy line** (kind `lazy line`, banned, rule `lazy 'start on Monday' line`). Every match in the scan line, ignoring case, of `\b(?:start|starting|begin|try|do)\b[^.!?\n]{0,40}\b(?:on|from|this|next)\s+Monday\b|\bMonday morning\b`. Span: the matched text.
12. **Enumeration** (kind `enumeration`, banned, rule `no 'First... Second... Third...' enumeration in prose`). Take the trimmed scan line. If it matches `^first\b` (ignoring case), remember that a "first" line has been seen. Then, if it matches `^(second|secondly)\b` (ignoring case) and a "first" line has been seen on this or any earlier line, flag it. Span: the first 40 characters of the trimmed scan line. "Firstly" does not count as a "first" line; "Third" is never flagged.

Note: the emoji and checkmark rules do not overlap (the emoji rule excludes the checkmarks), but an arrow character U+27A1 is flagged only as an arrow.

## Part B. Rules applied to the whole text

Make the whole scan text: the text with the quote mask applied to the whole text (only when skip_quotes is on), then the URL mask. Find matches in it; the line of a match is 1 plus the number of LF characters before the match start. The span is the matched text cut to the stated length; it can contain a line break.

13. **Not X, Y** (kind `not X, Y`, banned, rule `contrast LLMism: 'That's not X. That's Y'`), ignoring case: `\b(?:that|it|this)(?:'s|\u2019s| is| was)\s+not\b[^.!?\n]{1,80}[.!?]\s+(?:that|it|this)(?:'s|\u2019s| is| was)\b|\b(?:that|it|this) (?:isn't|wasn't|isn\u2019t|wasn\u2019t)\b[^.!?\n]{1,80}[.!?]\s+(?:that|it|this)(?:'s|\u2019s| is| was)\b`. Span: the first 90 characters of the match.
14. **Not just** (kind `not X, Y`, banned, rule `contrast LLMism variant: 'not just X. They are Y'`), ignoring case: `\b(?:not|no longer|isn't|aren't|wasn't|weren't|isn\u2019t|aren\u2019t|wasn\u2019t|weren\u2019t|don't|doesn't|didn't|don\u2019t|doesn\u2019t|didn\u2019t|do not|does not)\s+(?:just|only|merely|simply)\b[^.!?\n;:\u2014\u2013]{1,80}(?:[.;:!?]|\s[\u2014\u2013]|\s-\s|,)\s*(?:but\s+)?(?:it|they|we|this|that|you)(?:'s|\u2019s|'re|\u2019re)?\b`. Span: the first 90 characters.
15. **Old and new** (kind `old/new`, review, rule `'Old thinking / New thinking' framing`), ignoring case: `\bold (?:thinking|way)\b[\s\S]{0,200}?\bnew (?:thinking|way)\b` (the shortest stretch from "old thinking" or "old way" to "new thinking" or "new way", at most 200 characters between). Span: the first 60 characters.

All matches of rule 13 come before all matches of rule 14, which come before rule 15; within a rule, left to right, matches do not overlap.

## Part C. Fragments and questions

A prose line is a raw line that is not blank and is not a heading or label. A line is a heading or label when its trimmed text starts with "#", "|", "-", "*" or ">", or matches `^[A-Z][A-Za-z /]{0,30}:\s` (a capital letter, up to 30 letters, spaces or slashes, a colon and white space, such as "Note: ..."). The last prose line is the prose line with the highest line number.

For each prose line, in order: take the raw line (with the quote mask applied to the line when skip_quotes is on; the URL mask is not applied here), trim it, and split it at every run of white space that directly follows ".", "!" or "?" (`(?<=[.!?])\s+`). For each piece, in order:

16. **Fragment** (kind `fragment`, review, rule `staccato fragment of 1 to 3 words`): count the matches of `[A-Za-z0-9'\u2019]+` in the piece. If the count is 1, 2 or 3 and the piece ends with "." or "!", flag it. Span: the piece.
17. **Question** (kind `question`, review, rule `rhetorical question in the body; a real open question at the close is fine`): if the piece ends with "?" and this line is not the last prose line, flag it. Span: the first 80 characters of the piece.

## Part D. Weekday next to a date

Run on the original text (no masks). Two patterns, both ignoring case, each run over the whole text, the first pattern's matches before the second's:

- `\b(?P<wd>mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?,?\s+(?P<d>\d{1,2})(?:st|nd|rd|th)?\s+(?P<m>[a-z]{3,9})\.?,?\s+(?P<y>\d{4})\b` (weekday, day, month, year: "Thursday, 13 May 2026", "Thu 13 May 2026")
- `\b(?P<wd>mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?,?\s+(?P<m>[a-z]{3,9})\.?\s+(?P<d>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<y>\d{4})\b` (weekday, month, day, year: "Thursday, May 13, 2026")

For each match: the month is the month whose first three letters equal the first three letters of the month word, in lower case (so "Sept" and "September" are September); if none, skip the match. The weekday said is the weekday whose first three letters are the wd letters (any word starting with those three letters counts, so "Thurs" is Thursday). If day, month and year do not form a real calendar date (for example 31 February, day 0, year 0000), flag `not a real date`. Otherwise, if the real weekday of that date differs from the weekday said, flag `that date is a ` + the real weekday name in English with a capital first letter (for example `that date is a Wednesday`).

18. **Date** (kind `date`, banned). Span: the whole matched text. Rule: as above. Line: 1 plus the number of LF characters before the FIRST place the span's text appears anywhere in the text. So when the same wrong date is written twice, both flags carry the line of the first one.

## Order of flags

Collect the flags in the order the rules above add them (Part A line by line, then Part B, then Part C, then Part D). Then sort them by line number, and within a line by kind, comparing the kind texts character by character by code point (so the order of kinds is: arrow, banned word, checkmark, dash, date, emoji, encoding, enumeration, exclamation, fragment, lazy line, not X, Y, old/new, question, review word, self label, unicode bold). The sort is stable: flags with the same line and kind keep their collected order.

## Counts and the reading grade

| Count | How |
|---|---|
| characters | The number of characters in the text after removing LF characters from its end only. |
| words | The number of runs of characters that are not white space (`\S+`) in the text. |
| sentences | The number of sentences in the text (below). |
| approx_reading_grade | The grade (below), or none. |
| approx_band | From the grade (below). |
| banned_flags | The number of flags with severity banned. |
| review_flags | The number of flags with severity review. |

**Sentences** of a text: split it at every run of white space that directly follows ".", "!" or "?", and at every run of two or more LF characters (`(?<=[.!?])\s+|\n{2,}`); trim each piece; keep only the pieces that contain at least one letter A to Z or a to z.

**Grade.** Use the text with the quote mask applied to the whole text when skip_quotes is on (no URL mask). Its sentences are counted as above. Its words are the matches of `[A-Za-z][A-Za-z'\u2019-]*` (a letter A to Z followed by letters, apostrophes and hyphens). If there are no sentences or no words, the grade is none. Otherwise, for each word, its syllables: lower case it and remove everything that is not a to z; count the runs of the vowels a, e, i, o, u, y; if the word ends in "e" but not in "le", "ee" or "ye", and the count is above 1, subtract 1; the result is at least 1. Then

grade = 0.39 x (words / sentences) + 11.8 x (syllables / words) - 15.59

computed in ordinary double precision floating point and rounded to one decimal place the way Python `round(x, 1)` does. It can be negative.

**Band:** none gives `not enough text`; below 10 gives `secondary school`; 10 up to but not including 13 gives `upper secondary`; 13 up to but not including 17 gives `graduate`; 17 or above gives `above graduate`.

## Printed output (text)

Line by line:

| Line | Exact shape |
|---|---|
| 1 | `characters <characters> \| words <words> \| sentences <sentences> \| approximate reading grade <grade> (<band>, an estimate)` |
| 2 | `banned flags <banned_flags> \| review flags <review_flags>` |
| one per flag | `line <line> \| <severity> \| <kind> \| <quoted span> \| <rule>` |
| last, only when there are no flags | `no flags` |

(In this table "\|" stands for a plain vertical bar.) Details:

- The grade is written with at least one decimal, the way Python prints a float: 7.0, 12.5, -0.3, 0.0. No grade is written `None`.
- `<line>` is right aligned in 3 characters (padded with spaces on the left; a number of 4 or more digits is written as is). `<severity>` is `banned` or `review`. `<kind>` is padded with spaces on the right to 12 characters.
- `<quoted span>` is the span written the way Python `repr()` writes a string. It is wrapped in single quotes, unless the span contains a single quote and no double quote, in which case it is wrapped in double quotes. Inside: a backslash is written `\\`; the wrapping quote character is written with a backslash before it; a tab, LF and CR are written `\t`, `\n`, `\r`; any other character that is not printable (Unicode categories Cc, Cf, Cs, Co, Cn, Zl, Zp, and every space separator except the plain space U+0020, such as the no break space U+00A0) is written `\x` plus 2 lower case hex digits when its code is below 0x100, `\u` plus 4 hex digits when below 0x10000, otherwise `\U` plus 8 hex digits. Every other character, accented letters, curly quotes, emoji and dashes included, is written as itself.

## Printed output (JSON, for API or programmatic use)

One object, written the way Python `json.dumps(obj, ensure_ascii=False, indent=2)` writes it: two spaces of indent per level, every key and list item on its own line, ": " between key and value, "," at the end of every line but the last in an object or list, an empty list written `[]`. Characters outside ASCII are written as themselves; a double quote, a backslash and control characters inside strings are escaped (`\"`, `\\`, `\n`, `\t`, `\r`, `\b`, `\f`, and `\u00XX` with lower case hex for the other control characters).

Keys, in this order: "stats", an object with "characters", "words", "sentences", "approx_reading_grade" (a number written with at least one decimal, such as 3.0, or null), "approx_band", "banned_flags", "review_flags"; then "flags", a list with one object per flag, keys "line", "kind", "severity", "span", "rule", in that order, flags in the sorted order.

## Worked example

The text, three lines (the hyphen on line 3 is a keyboard hyphen with a space on each side), skip_quotes off:

```
We closed the round! It works.
That's not a tool. That's a habit.
We leverage AI on Thursday, 13 May 2026 - fast.
```

- Characters 113, words 23 (white space runs), sentences 5: "We closed the round!", "It works.", "That's not a tool.", "That's a habit.", and line 3 whole.
- Grade: 20 words by the grade pattern ("13" and "2026" are not words; "-" is not), 25 syllables ("closed" 2, "habit" 2, "leverage" 3, "Thursday" 2, every other word 1). 0.39 x 20/5 + 11.8 x 25/20 - 15.59 = 0.72, rounded 0.7: secondary school.
- 13 May 2026 is a Wednesday, so "Thursday, 13 May 2026" is flagged.
- Line 2: "That's a habit." has 3 words and ends with ".", so it is a fragment; "That's not a tool." has 4 (That's, not, a, tool), so it is not.
- Line 3: the scan line has no masks to apply; the dash span runs 15 characters either side of the hyphen, then is trimmed.

Printed text, line by line:

```
characters 113 | words 23 | sentences 5 | approximate reading grade 0.7 (secondary school, an estimate)
banned flags 5 | review flags 2
line   1 | banned | exclamation  | 'We closed the round!' | no exclamation marks in published text
line   1 | review | fragment     | 'It works.' | staccato fragment of 1 to 3 words
line   2 | review | fragment     | "That's a habit." | staccato fragment of 1 to 3 words
line   2 | banned | not X, Y     | "That's not a tool. That's" | contrast LLMism: 'That's not X. That's Y'
line   3 | banned | banned word  | 'leverage' | banned word or phrase: leverage
line   3 | banned | dash         | 'y, 13 May 2026 - fast.' | no long, short or spaced dashes
line   3 | banned | date         | 'Thursday, 13 May 2026' | that date is a Wednesday
```

The same text in JSON starts:

```
{
  "stats": {
    "characters": 113,
    "words": 23,
    "sentences": 5,
    "approx_reading_grade": 0.7,
    "approx_band": "secondary school",
    "banned_flags": 5,
    "review_flags": 2
  },
  "flags": [
    {
      "line": 1,
      "kind": "exclamation",
      "severity": "banned",
      "span": "We closed the round!",
      "rule": "no exclamation marks in published text"
    },
```

A second check, the one line draft of Example 2 in SKILL.md ("In today's world, IT teams need robust tools to navigate change. Our platform empowers them to unlock seamless service."): banned words are listed in list order, not text order, so "unlock", "seamless" and "empowers" come before "In today's world" and "robust":

```
characters 119 | words 19 | sentences 2 | approximate reading grade 6.1 (secondary school, an estimate)
banned flags 5 | review flags 1
line   1 | banned | banned word  | 'unlock' | banned word or phrase: unlock
line   1 | banned | banned word  | 'seamless' | banned word or phrase: seamless
line   1 | banned | banned word  | 'empowers' | banned word or phrase: empowers
line   1 | banned | banned word  | "In today's world" | banned word or phrase: in today's world
line   1 | banned | banned word  | 'robust' | banned word or phrase: robust
line   1 | review | review word  | 'navigate' | banned for abstract things; fine for a literal route
```

## Results in short

| Result | Meaning |
|---|---|
| `banned flags 0` and `no flags` | The text passes the mechanical scan. Still read it against references/banned-words-and-patterns.md, section 3, because the scan does not catch every pattern. |
| one or more banned flags | Fix each one (or keep it on the writer's decision, said once) and scan again. |
| review flags only | Decide each: literal use (keep) or filler (fix). |
