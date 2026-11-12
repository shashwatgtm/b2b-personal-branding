# Field counts and number lock: the method

This file sets out one fixed check for personal brand assets kept in one text where each asset starts with a "## " heading (for example "## Headline", "## Short bio"): characters and words per field, the same counts without the draft labels, open placeholders, dashes, numbers with the word after them, limits, labels that carry different numbers across fields, and wrong weekdays next to dates. Follow the rules exactly. When code execution is available, write your own calculation from these rules and run it; otherwise work it out by hand and say "counted by hand per the method". Either way the printed lines must match the shapes below character for character.

Limits are never assumed. A limit comes from the person or the platform's own help page, and is a whole number of characters for a field that is a "## " heading in the text. A word target is not a limit: compare it with the word count.

The patterns below are written as Python regular expressions (the `re` module, with its default Unicode behaviour: `\w` is any Unicode letter, digit or underscore, `\s` is any Unicode white space, `\d` is any Unicode decimal digit, `\b` is a word boundary). A code implementation should use them as written. By hand, read each pattern by its plain English gloss.

## Inputs

| Input | Required | Meaning |
|---|---|---|
| text | yes | The assets. When it comes from a file, read it as UTF-8, replace any byte that is not valid UTF-8 with U+FFFD, and turn every CR LF pair and every lone CR into LF. A byte order mark at the start is kept as the character U+FEFF (so a first line "## Headline" right after a byte order mark is not a field). |
| limits | no | Zero or more limits, each written "Field=number", in the order given, exactly as the user wrote them. |
| format | no (default text) | text or json. |

## Rules, in this order

Stop at the first rule that refuses. A refusal prints one line and nothing else.

### 1. Read the limits

For each limit in order, split it at its first "=". Trim the field part and the number part of white space at both ends. The limit is bad when there is no "=", or the trimmed field part is empty, or the trimmed number part is not made only of the ASCII digits 0 to 9 (an empty number part, a sign, a decimal point, a letter or a non ASCII digit all fail), or it has more than 9 digits. At the first bad limit, refuse with:

`bad --limit <the limit as written, quoted>: use Field=number of characters, for example --limit "Headline=220" (a word target is not a limit: compare it with the word count this script prints)`

(The quoted limit is written the way Python `repr()` writes a string; see Quoting.) Otherwise the limit is field part to the whole number (leading zeros dropped: "007" is 7). When two limits have the same field part, the later one wins.

### 2. Split the fields

Split the text into lines the way Python `str.splitlines()` does (at LF, and also at U+000B, U+000C, U+001C, U+001D, U+001E, U+0085, U+2028 and U+2029). A line that begins "## " (two "#" and a space; "### " does not count) starts a field; the field's name is the rest of the line after those three characters, trimmed. The following lines up to the next field line are its body: joined with LF, then trimmed of white space at both ends. Lines before the first field line are not counted. If the text has no field line at all, the whole text, trimmed, is one field named `Text`. Fields with the same name stay separate fields.

### 3. Check that each limit names a field

Compare in lower case. Every limit whose field part, in lower case, is not the lower case name of some field is unknown. If any is unknown, refuse with:

`bad --limit: no field named <names> in the file; fields are: <fields>`

where `<names>` is each unknown field part (as trimmed, original case) quoted the Python `repr()` way, joined by ", ", in the order the limits were given (a field part written exactly the same way twice is listed once), and `<fields>` is every field name in field order joined by ", ".

### 4. Count each field

For each field, in order:

| Count | How |
|---|---|
| characters | The number of characters in the body. |
| words | The number of runs of characters that are not white space (`\S+`) in the body. |
| final text | The body with every draft label replaced by its drafted words trimmed (pattern D below), then every principal marker removed together with the white space before it (pattern M), then every run of two or more spaces or tabs replaced by one space, then trimmed. |
| final_characters | The number of characters in the final text. |
| final_words | The number of `\S+` runs in the final text. |
| draft_labels | The number of pattern D matches plus the number of pattern M matches in the body. |
| placeholders_open | The number of pattern P matches in the body. |
| dashes | For every dash match in the body (pattern H), the body from (match start minus 12) to (match end plus 12), not trimmed; a start below 0 is 0. |
| numbers | The numbers in the body (below), each in its display form. |

All three of these patterns ignore case:

- D, draft label: `\[Draft for you to confirm:\s*((?:[^\[\]]|\[[^\[\]]*\])*)\]`. "[Draft for you to confirm:", optional white space, the drafted words (which may hold one level of brackets, such as "[Name]" or a "[User to add: ...]" placeholder), then "]". The drafted words are the part in the inner group.
- M, principal marker: `\s*\[Principal to confirm\]`.
- P, open placeholder: `\[User to add:[^\[\]]*\]`.

H, dash: `[\u2012\u2013\u2014\u2015]|(?<=\s)-(?=\s)|\s--\s`. A figure dash, en dash, em dash or horizontal bar; a single hyphen with white space directly on both sides; or two hyphens with white space on both sides (included in the match). A bullet "- item" on a later line of a body counts (the line break before it is white space); a hyphen at the very first character of a body does not.

**Numbers.** Every match in the body of

`(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)([ \t]?%|\+)?(?:[ \t]+([A-Za-z]+))?`

In words: a number not directly after a word character or a full stop; digits grouped by commas in threes ("1,200") or digits with an optional decimal part ("3.5"); then optionally a percent sign (at most one space or tab before it) or a plus sign; then optionally spaces or tabs and a word of the letters A to Z. For each match:

- value: the number exactly as written, commas kept ("1,200"), followed by "%" if it had a percent sign or "+" if it had a plus sign ("40 %" gives "40%").
- label: the word in lower case, or empty. If the word is one of: and, or, the, a, an, to, of, in, on, at, for, with, by, from, as, the label is empty.
- display form: the value, then a space and the label when there is a label ("24 years", "40% growth", "37+ engagements"), else the value alone ("10%", "2026").

**Limit.** When the field's name in lower case equals the field part of a limit in lower case, the field has that limit (the later one when two match), and over_limit_by is final_characters minus the limit, or 0 when that is negative. Limits are always checked on final_characters.

### 5. Label conflicts

For each number with a label, record that this label carries this value in this field (by field name). Then, for each label in sorted order that carries 2 or more different values, list each value in sorted order with the sorted names of the fields it appears in (each name once). Sorting compares strings character by character by code point, so "12" comes before "9" and "14" before "14%".

### 6. Weekday next to a date

Run on the whole text (not field by field). Two patterns, both ignoring case, each run over the whole text, all matches of the first before all matches of the second:

- `\b(?P<wd>mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?,?\s+(?P<d>\d{1,2})(?:st|nd|rd|th)?\s+(?P<m>[a-z]{3,9})\.?,?\s+(?P<y>\d{4})\b` (weekday, day, month, year)
- `\b(?P<wd>mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?,?\s+(?P<m>[a-z]{3,9})\.?\s+(?P<d>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<y>\d{4})\b` (weekday, month, day, year)

For each match: the month is the month whose first three letters equal the first three letters of the month word in lower case; if none, skip it. The weekday said is the weekday whose first three letters are the wd letters. If day, month and year are not a real calendar date, the problem is `not a real date`. Otherwise, if the real weekday differs from the weekday said, the problem is `that date is a ` + the real weekday in English with a capital first letter. The span is the whole matched text.

## Quoting

A quoted string is written the way Python `repr()` writes it: wrapped in single quotes, unless it contains a single quote and no double quote, in which case double quotes. Inside: a backslash is `\\`; the wrapping quote character gets a backslash before it; tab, LF and CR are `\t`, `\n`, `\r`; any other non printable character (Unicode categories Cc, Cf, Cs, Co, Cn, Zl, Zp, and every space separator except the plain space, such as U+00A0) is `\x` plus 2 lower case hex digits below 0x100, `\u` plus 4 below 0x10000, else `\U` plus 8. Everything else, dashes and accented letters included, is written as itself. A Python list is "[", each item quoted this way and joined by ", ", then "]".

## Printed output (text)

For each field, in order:

| Line | Exact shape | When |
|---|---|---|
| field line | `<name>: <characters> characters, <words> words` then `; without the draft labels: <final_characters> characters, <final_words> words` when draft_labels is above 0, then `, limit <limit>` and either `, OVER by <over_limit_by>` (when above 0) or `, within limit`, when the field has a limit | Always. "characters" and "words" stay plural even for 1 or 0. |
| placeholders | `  placeholders still open: <n> (the count changes when they are filled)` | When placeholders_open is above 0. |
| dashes | `  dashes: <the dash snippets as a Python list>` | When there are dashes. |
| numbers | `  numbers: <display forms joined by ", ">` | When there are numbers. |

Then:

| Line | Exact shape | When |
|---|---|---|
| conflict header | `Check these: the same label carries different numbers across fields` | When there is at least one conflict. |
| one per conflict | `  <label>: <value> in <fields>; <value> in <fields>` | Fields joined by ", "; value groups joined by "; ". |
| no conflict | `No label carries two different numbers across fields.` | When there is no conflict. |
| one per date problem | `Date problem: <quoted span>: <problem>` | In the order found. |

## Printed output (JSON, for API or programmatic use)

One object, written the way Python `json.dumps(obj, ensure_ascii=False, indent=2)` writes it: two spaces of indent per level, every key and list item on its own line, ": " between key and value, an empty list written `[]`, characters outside ASCII written as themselves, and `\"`, `\\`, `\n`, `\t`, `\r`, `\b`, `\f` or `\u00XX` (lower case hex) for quotes, backslashes and control characters.

Keys, in this order: "fields", a list with one object per field (keys "field", "characters", "words", "final_characters", "final_words", "draft_labels", "placeholders_open", "dashes", "numbers", and then "limit" and "over_limit_by" only when the field has a limit); "label_conflicts", a list of objects with keys "label" and "values" (an object: value to sorted list of field names, values in sorted order); "weekday_errors", a list of objects with keys "span" and "problem". A refusal (rules 1 and 3) prints its one line, not JSON.

## Exit status

When the count runs as code, it ends with a status: 2 after a refusal (a `bad --limit` line from rule 1 or rule 3), and 0 otherwise, in text and JSON alike. A field over its limit, a label conflict or a date problem does not change the status: read the lines.

## Worked example

The text:

```
## Headline
Head of RevOps for B2B SaaS | 12 years in sales operations

## Short bio
I help sales teams forecast within 10% of actuals. 14 years in sales operations. [Draft for you to confirm: Based in Pune.] [Principal to confirm]

## Speaker bio
[User to add: current title] with 12 years in revenue teams, speaking on Thursday, 10 December 2026.
```

with the limits "Headline=220" and "Short bio=100".

- Short bio: the body has 146 characters and 25 words. The draft label becomes "Based in Pune.", the marker and the space before it go: final text 95 characters, 17 words; 2 draft labels (one label, one marker). The limit 100 is checked on 95: within limit.
- "10% of": the percent sign stays on the value, and "of" is a stop word, so the display form is "10%".
- "12 years" (Headline, Speaker bio) and "14 years" (Short bio): the label "years" carries two values.
- "10 December 2026" gives "10 december" and "2026" as numbers; 10 December 2026 is a Thursday, so no date problem.

Printed text, line by line:

```
Headline: 58 characters, 12 words, limit 220, within limit
  numbers: 12 years
Short bio: 146 characters, 25 words; without the draft labels: 95 characters, 17 words, limit 100, within limit
  numbers: 10%, 14 years
Speaker bio: 100 characters, 17 words
  placeholders still open: 1 (the count changes when they are filled)
  numbers: 12 years, 10 december, 2026
Check these: the same label carries different numbers across fields
  years: 12 in Headline, Speaker bio; 14 in Short bio
```

A refusal: with the limit "Short bio=50w" the only line printed is

```
bad --limit 'Short bio=50w': use Field=number of characters, for example --limit "Headline=220" (a word target is not a limit: compare it with the word count this script prints)
```

and with the limit "Tagline=100" on the same text it is

```
bad --limit: no field named 'Tagline' in the file; fields are: Headline, Short bio, Speaker bio
```

## Results in short

| Result | Meaning |
|---|---|
| a `bad --limit` line | The limit was refused; ask the user for a whole number of characters for a field in the text. |
| `OVER by N` | Cut the field by at least N characters, counted without the draft labels, and check again. |
| a conflict | Fix every asset to the fact sheet value, then check again. |
| a `Date problem` line | Ask the person; never change a date silently. |
