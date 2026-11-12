# Issue and asset check: the method

This file sets out one fixed check for a newsletter issue and its derived assets (share card text, subject lines, a teaser post): curated items without a link, every number with the word after it, numbers in an asset that are not in the issue (drift), labels that carry different numbers across files, wrong weekdays next to dates, dashes, and character counts per section and per line. Follow the rules exactly. When code execution is available, write your own calculation from these rules and run it; otherwise work it out by hand and say "counted by hand per the method". Either way the printed lines must match the shapes below character for character.

The check does not open links. Opening each link is a separate step, done with the chat's web tools, and reported per link. Spelled out numbers ("three launches") are not caught; check them by reading.

The patterns below are written as Python regular expressions (the `re` module, with its default Unicode behaviour: `\w` is any Unicode letter, digit or underscore, `\s` is any Unicode white space, `\d` is any Unicode decimal digit, `\b` is a word boundary). A code implementation should use them as written. By hand, read each pattern by its plain English gloss.

## Inputs

| Input | Required | Meaning |
|---|---|---|
| issue | yes | The issue text. Each curated item starts with a line that begins "### ". |
| derived | no | Zero or more derived assets, in the order given. Each has a name (the file name as the user gave it) and a text. |
| deep_dive | no (default off) | On for a deep dive issue: one topic, no "### " curated items. |
| format | no (default text) | text or json. |

Every text that comes from a file is read as UTF-8 with a byte order mark at the start removed, any byte that is not valid UTF-8 replaced by U+FFFD, and every CR LF pair and every lone CR turned into LF.

The files, in order, are the issue (always named `issue`) and then each derived asset under its own name.

## Building blocks

**URL.** A match of `https?://\S+`: "http://" or "https://" up to the next white space. "www." alone is not a URL here.

**URL stripped text.** The text with every URL replaced by one single space.

**Numbers in a text.** Find, in the URL stripped text, every match of

`(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)([ \t]?%|\+)?(?:[ \t]+([A-Za-z]+))?`

In words: a number not directly after a word character or a full stop; either digits grouped by commas in threes ("1,200") or digits with an optional decimal part ("2.5"); then optionally a percent sign (with at most one space or tab before it) or a plus sign; then optionally spaces or tabs and a word made of the letters A to Z (the label). For each match:

- value: the number with its commas removed ("1,200" gives "1200"; "2.50" stays "2.50").
- label: the word in lower case, or empty. If the word is one of: and, or, the, a, an, to, of, in, on, at, for, with, by, from, as, is, the label is empty.
- If the number had a percent sign, the label is "%" (whatever word followed).
- If the number had a plus sign, "+" is added to the end of the value ("500+").

Each number is written for display as: the value, then a space and the label when the label is a word; the value then "%" when the label is "%"; the value alone when the label is empty. So "40 %" and "40%" both display as `40%`, "1,200 customers" as `1200 customers`, "500+ deployments" as `500+ deployments`.

**A year-like value** is exactly four characters: "19" or "20" followed by two digits (so "2026" is year-like, "2026+" is not).

**Curated items.** First remove every fenced code block from the issue: a match of `(?ms)^(```|~~~).*?^\1[^\n]*$` (from a line starting with three backticks or three tildes to the next line starting with the same three characters, through the end of that line; an unclosed fence is not removed). Then split the remaining text at every line start that begins "### " (`(?m)^### `), and drop the first piece (the text before the first item). Each remaining piece is one item. The item count is the number of pieces.

For each item: its title is its first line, trimmed of white space at both ends; when the whole piece is only white space, its title is `(empty item)`. An item is "without a link" when it contains no URL. An item is "untitled" when its first line is empty after trimming (an empty piece counts as untitled).

**Sections, for the field counts.** Go through the file line by line (the original text, code blocks included). A line that begins "## " or "### " (exactly: two or three "#" then a space; "#### " does not count) starts a section; its name is the line with all "#" characters removed from its start and then trimmed. The following lines, up to the next section line, are its body. Lines before the first section line belong to no section. For each section: body = its lines joined with LF, trimmed; characters = the number of characters in that body. Then take the body's lines, each trimmed, leaving out empty ones: when there are 2 to 8 such lines, list each with its own character count.

**Dashes.** In the URL stripped text, every match of `[\u2012\u2013\u2014\u2015]|(?<=\s)-(?=\s)|\s--\s`: a figure dash, en dash, em dash or horizontal bar; a single hyphen with white space directly on both sides; or two hyphens with white space on both sides (included in the match). A bullet "- item" at the start of a line counts (the line break before it is white space), except at the very first character of the file. For each match, the snippet is the URL stripped text from (match start minus 12) to (match end plus 12), not trimmed (a start below 0 is 0).

**Weekday next to a date.** Run on the file's text as read (URLs not stripped). Two patterns, both ignoring case, each run over the whole text, all matches of the first before all matches of the second:

- `\b(?P<wd>mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?,?\s+(?P<d>\d{1,2})(?:st|nd|rd|th)?\s+(?P<m>[a-z]{3,9})\.?,?\s+(?P<y>\d{4})\b` (weekday, day, month, year)
- `\b(?P<wd>mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?,?\s+(?P<m>[a-z]{3,9})\.?\s+(?P<d>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<y>\d{4})\b` (weekday, month, day, year)

For each match: the month is the month whose first three letters equal the first three letters of the month word in lower case; if none, skip it. The weekday said is the weekday whose first three letters are the wd letters. If day, month and year are not a real calendar date, the problem is `not a real date`. Otherwise, if the real weekday differs from the weekday said, the problem is `that date is a ` + the real weekday in English with a capital first letter. The span is the whole matched text.

## Rules, in this order

1. Items: count the curated items and list the titles of the items without a link, in item order.
2. Issue values: the set of values of the numbers in the issue.
3. For each file in order (the issue first, then the derived assets in the order given):
   - numbers: the display form of each number, in order of appearance;
   - characters: the number of characters in the whole text trimmed of white space at both ends;
   - field counts: the sections, if the file has any;
   - dashes: the snippets, if any;
   - weekday problems: each with the file name;
   - then for each number, in order, skipping year-like values: in a derived asset (any file not named `issue`), a value not in the issue values is drift (file, value, label); and when the label is not empty, record that this label carries this value in this file.
4. Label conflicts: for each label, in sorted order, that carries 2 or more different values: list each value, in sorted order, with the sorted names of the files it appears in. Sorting compares strings character by character by code point, so "12" comes before "9", "%" before any letter, and "cases/a.txt" before "issue".
5. Problems, in this order: `the issue is empty` when the issue is only white space; `0 curated items found: each item must start with a '### ' heading` when the item count is 0 and deep_dive is off; `<n> item heading(s) with no title: write the item's headline after '### '` when n items are untitled.
6. Pass: true only when there are no problems, no items without a link, no drift, no label conflicts, no weekday problems and no dashes in any file.

## Printed output (text)

Line by line:

| Line | Exact shape | When |
|---|---|---|
| 1 | `curated items: <count>; without a link: <list or none>` | Always. The list is written as a Python list (below); `none` when no item lacks a link. |
| per file | `<name>: <characters> characters; numbers: <numbers>` | One per file, in file order. `<numbers>` is the display forms joined by ", ", or `none`. |
| per section | `  field <section name>: <characters> characters` | Under its file's line, two spaces first. A section with an empty name prints `  field : <n> characters`. |
| per section line | `    <characters> \| <line text>` | Under its section, only for sections with 2 to 8 lines: four spaces, the count right aligned in 4 characters, a space, a vertical bar, a space, the trimmed line. |
| per drift | `DRIFT: <file> has <value> <label> which is not in the issue` | In collected order. An empty label leaves two spaces: `has 80  which`. |
| per conflict | `CONFLICT: '<label>' carries <value> in <files>; <value> in <files>` | `<files>` joined by ", "; value groups joined by "; ". |
| per weekday problem | `DATE: <file>: <quoted span>: <problem>` | In collected order. |
| per file with dashes | `DASH: <name>: <snippet list>` | In file order; the snippets written as a Python list. |
| per problem | `PROBLEM: <problem>` | In the order of rule 5. |
| last | `PASS` or `FIX the items above, then run again` | Always. |

**Quoted span and Python lists.** A quoted span is written the way Python `repr()` writes a string: wrapped in single quotes, unless it contains a single quote and no double quote, in which case double quotes. Inside: a backslash is `\\`; the wrapping quote character gets a backslash before it; tab, LF and CR are `\t`, `\n`, `\r`; any other non printable character (Unicode categories Cc, Cf, Cs, Co, Cn, Zl, Zp, and every space separator except the plain space, such as U+00A0) is `\x` plus 2 lower case hex digits below 0x100, `\u` plus 4 below 0x10000, else `\U` plus 8. Everything else, dashes and accented letters included, is written as itself. A Python list is "[", the items each written as a quoted span and joined by ", ", then "]".

## Printed output (JSON, for API or programmatic use)

One object, written the way Python `json.dumps(obj, ensure_ascii=False, indent=2)` writes it: two spaces of indent per level, every key and list item on its own line, ": " between key and value, an empty list written `[]` and an empty object `{}`, characters outside ASCII written as themselves, and `\"`, `\\`, `\n`, `\t`, `\r`, `\b`, `\f` or `\u00XX` (lower case hex) for quotes, backslashes and control characters.

Keys, in this order:

| Key | Value |
|---|---|
| items | the item count |
| items_without_link | list of titles |
| numbers | object: file name to list of display forms, every file in file order |
| drift | list of objects with keys file, value, label |
| label_conflicts | list of objects with keys label, values (an object: value to sorted list of file names, values in sorted order) |
| weekday_errors | list of objects with keys file, span, problem |
| dashes | object: file name to list of snippets, only files that have dashes |
| field_counts | object: file name to list of section objects (keys field, characters, and lines only when there are 2 to 8 lines: a list of objects with keys text, characters), only files that have sections |
| characters | object: file name to character count, every file |
| problems | list of problem texts; this key is present only when there is at least one problem |
| pass | true or false |

## Exit status

When the check runs as code, it ends with a status: 0 when the result is `PASS` (in JSON, "pass" is true), 1 when it is `FIX the items above, then run again` (in JSON, "pass" is false), and 2 when a file could not be read. Before any check, every file is read, the issue first and then each derived file in the order given; if one cannot be opened, the only line printed (in text and JSON alike) is `cannot read a file: [Errno <n>] <system message>: '<path as given>'`, for a missing file `cannot read a file: [Errno 2] No such file or directory: 'teaser.txt'`.

## Worked example

The issue:

```
### Observe.AI ships Companion Agent
Announced May 13, 2026 with 1,200 customers and 500+ deployments.
https://www.prnewswire.com/news-releases/observeai-302770347.html
```

and one derived asset named `teaser.txt`:

```
1,200 customers, 80% of them in India.
Thursday, May 13, 2026.
```

- Items: 1, with a link.
- Issue numbers: "13" (label empty: "2026" is not a word), "2026" (the word after "2026 " is "with", a stop word, so the label is empty), "1200 customers", "500+ deployments". The URL is stripped before numbers are found, so its digits do not count.
- Teaser numbers: "1200 customers", "80%" (the word after is "of", but the percent sign makes the label "%"), "13", "2026". Drift: 80 with label "%" is not in the issue. "2026" is year-like and skipped. "13" is in the issue.
- 13 May 2026 is a Wednesday, so "Thursday, May 13, 2026" is a weekday problem.
- The issue has one section (the "### " line), body 2 lines, so both lines are listed.

Printed text, line by line:

```
curated items: 1; without a link: none
issue: 168 characters; numbers: 13, 2026, 1200 customers, 500+ deployments
  field Observe.AI ships Companion Agent: 131 characters
      65 | Announced May 13, 2026 with 1,200 customers and 500+ deployments.
      65 | https://www.prnewswire.com/news-releases/observeai-302770347.html
teaser.txt: 62 characters; numbers: 1200 customers, 80%, 13, 2026
DRIFT: teaser.txt has 80 % which is not in the issue
DATE: teaser.txt: 'Thursday, May 13, 2026': that date is a Wednesday
FIX the items above, then run again
```

## Results in short

| Result | Meaning |
|---|---|
| `PASS` | Every item has a link, every number in the assets is in the issue, no label carries two numbers, weekdays are right and there are no dashes. Still open each link with the web tools, and check spelled out numbers by reading. |
| `FIX the items above, then run again` | Fix each DRIFT to the sourced figure in the issue, each CONFLICT, DATE, DASH and PROBLEM line, add the missing links, and check again. |
