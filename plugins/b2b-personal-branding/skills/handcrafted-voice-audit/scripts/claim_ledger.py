#!/usr/bin/env python3
"""Claim ledger (1.0.3): lists every line of the text you are about to deliver that states a fact about the
user, a named company, a person or a buyer seat, or carries a figure or an absence claim, and checks the
ledger of sources you wrote for those lines. Python 3 standard library only; reads files, writes nothing,
sends nothing.

Use (python3, or python on Windows):
  claim_ledger.py list  ANSWER [SAVED ...]
  claim_ledger.py check ANSWER [SAVED ...] --ledger LEDGER [--opened OPENED] [--prompt PROMPT]
                        [--script-out FILE ...]

ANSWER is the chat answer exactly as it will be delivered; SAVED are the files saved for the user.
LEDGER has one line per entry:   <id>[,<id>...] | <source> | <detail>
  source user     the user's own message (--prompt file); figures must be in it and the line must keep
                  mostly the words of one of the user's sentences
  source page     detail: the URL(s) opened in this session (each must be in --opened)
  source script   detail: optional; every figure must appear in a --script-out file
  source notes    detail: a file in this skill's references folder; the line must be hedged or say
                  "notes"
  source general  a hedged general statement ("often", "may", "worth checking"), naming no company
  source absence  detail: <word> | <url> <url> ...; each URL must be in --opened with that word under
                  "checked:", and the line must name the pages it checked
  source self     a line that says only what this answer did ("I left out ...", "I opened ..."); it starts with I
  source search   always refused: label the line "from a search result, page not opened" or leave it out
OPENED has one line per page opened in this session:  <url> [| checked: <word>, <word>]
Exit code: 0 PASS, 1 FAIL, 2 bad input.
"""
import difflib, hashlib, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))

LABEL_SPAN_START = re.compile(r"\[(?=quote from\b|[^\[\]]{0,60}?(?:\bto (?:add|confirm|supply|set|fill|provide|approve|choose|check)\b|\bdraft\b|\bplaceholder\b))", re.I)
LINE_LABEL = re.compile(r"as pasted, not yet checked|not yet checked|from a search result|page (?:itself )?(?:was )?not opened|"
                        r"\bplaceholder\b|\bhypothetical\b|\bassumption\b|draft for you to confirm|user to add|to confirm\]|for you to confirm", re.I)
SEARCH_LABEL = re.compile(r"from a search result|search result.{0,40}not opened|page (?:itself )?(?:was )?not opened", re.I)
ABSENCE = re.compile(r"\b(?:does ?n[o']t|did ?n[o']t|do ?n[o']t|is ?n[o']t|are ?n[o']t|was ?n[o']t|never) (?:mention|say|list|show|state|name|appear|include|use)s?\b|"
                     r"\bno mention\b|\bnot mentioned\b|\bnot (?:found|listed|shown|stated|named)\b|\bfound no\b|\bnowhere\b|\bno (?:sign|trace|record) of\b|"
                     r"\b(?:is|are) not on\b|\bis ?n't on\b|\babsent from\b|\bmissing from\b|\bha(?:s|ve) no\b|\blacks?\b|"
                     r"\bdid ?n[o']t find\b|\bnothing (?:about|on|in)\b|\bha(?:s|ve) ?n[o']t (?:published|posted|said|shared|listed|named|stated|announced)\b|\bnone of the\b|\b(?:is|are) not in\b|\bnever (?:talks|says|mentions|publishes|lists|shows|names)\b|\bdo(?:es)? ?n[o']t (?:offer|publish|have|provide|give|share)\b|\bhad no\b", re.I)
HEDGE = re.compile(r"\b(?:often|may|might|can|could|tends?|usually|sometimes|likely|perhaps|possibly|probably|worth (?:checking|asking|testing)|"
                   r"in many cases|some)\b", re.I)
SEAT = re.compile(r"\b(?:C[EFIMTO]Os?|CISOs?|CHROs?|CROs?|COOs?|CPOs?|VPs?|head of|directors?|buyers?|procurement|champions?|decision makers?|"
                  r"analysts?|journalists?|editors|reporters|investors?|founders?|marketers?|leaders|teams|committee|board)\b")
YOU_US = re.compile(r"\b(?:us|ours)\b")
YOU = re.compile(r"(?:^|[.:]\s|\*\*\s?)I(?:'ve| have)? (?:built|founded|grew|grow|led|lead|run|ran|own|owned|cut|launched|started|sold|sell|manage|managed|"
                 r"joined|spent|host|hosted|speak|spoke|work|worked|helped|help|created|scaled|doubled|tripled|raised|won|hired|advise|advised|have \d)\b|\[Name\]|\b(?:we|our|we're|we've)\b|\byou(?:'ve|'re)? (?:are|were|have|had|lead|led|run|ran|own|built|spent|joined|work|worked|"
                 r"sell|sold|said|told|wrote|manage|managed|speak|spoke|launched|started|founded)\b|\byour (?:team|company|customers?|clients?|product|"
                 r"role|title|years|manager|ceo|founder|board|employer|launch|feature|event|talk|webinar|firm|business|buyers?|accounts?|pipeline)\b", re.I)
FIG = re.compile(r"\d")
LEAD_NAME = re.compile(r"[A-Z][A-Za-z0-9&.\-]*(?:'s)? (?:has|have|is|was|are|were|sells|sold|says|said|offers|ranks|ranked|provides|makes|runs|owns|requires|publishes|"
                       r"lists|launched|raised|serves|builds|uses|named|won|bought|acquired)\b")
WORD = re.compile(r"[A-Za-z][A-Za-z0-9&'.\-]*")
COMMON = set("""I I'm I've I'll I'd A An The This That These Those It Its It's If When Where What Which Who Why How And But Or Not No Yes Use Used Using
Here There Then Than Also Each Every All Any Some Most More Less One Two Three Four Five Six Seven Eight Nine Ten Do Don't Does Is Are Was Were Be Been
For From To In On At By With Without About After Before Between Into Over Under Up Down Out Only Just Still Even So As Of My Me Mine Your You You're
You've We We're Our Us They Their Them He She His Her Please Note Draft Open Items Item Question Questions Plan Source Sources Status Line Lines Check
Checks Fact Facts Notes Summary Option Options Step Steps Next Done Keep Add Make Send Ask Read See Say Write Copy Paste Run Before After Monday
Tuesday Wednesday Thursday Friday Saturday Sunday January February March April May June July August September October November December Mon Tue
Wed Thu Fri Sat Sun Jan Feb Mar Apr Jun Jul Aug Sep Sept Oct Nov Dec OK Q Subject Title Headline About Bio Short Medium Long Body Hook Opening Close
Call Why What's Who's Here's That's There's Let's Today Tomorrow Yesterday Near-final Confirmed Missing Needed""".split())
STOP = set("""the a an and or but of to in on at by for with from into over under about after before between this that these those it its is are was
were be been being have has had do does did will would shall should can could may might must not no yes you your yours we our us they their them he she
his her i me my mine who whom which what when where why how than then also just only very more most less least so as if each every all any some such
own same other there here name""".split())
ABBR = re.compile(r"\b(Inc|Ltd|Co|Corp|Pvt|e\.g|i\.e|vs|No|Dr|Mr|Ms|Mrs|St|Jr|Sr|approx|est)\.", re.I)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read().replace("\u2019", "'").replace("\u2018", "'").replace("\r\n", "\n")


def label_ranges(text):
    """Character ranges inside [Draft for you to confirm: ...], [User to add: ...] and similar brackets (nested brackets allowed)."""
    out = []
    for m in LABEL_SPAN_START.finditer(text):
        depth, i = 0, m.start()
        while i < len(text):
            if text[i] == "[":
                depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    break
            elif text[i] == "\n":   # an unclosed label ends at the end of its line (auditor item 3)
                break
            i += 1
        out.append((m.start(), i + 1))
    return out


def split_sentences(line):
    protected = ABBR.sub(lambda m: m.group(0)[:-1] + "\u0001", line)
    protected = re.sub(r"^(\s*(?:[-*]\s+)?\d{1,2})\.", lambda m: m.group(1) + "\u0001", protected)   # a list number is not a sentence end
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\[\"'(*_0-9])", protected)
    return [p.replace("\u0001", ".") for p in parts if p.strip()]


def units(text, fname):
    """(file, line number, text, labelled) for every sentence (table rows whole); code fences skipped."""
    ranges = label_ranges(text)
    res, pos, fence = [], 0, False
    lines = text.split("\n")
    for n, line in enumerate(lines, 1):
        start = pos
        pos += len(line) + 1
        if line.strip().startswith("```"):
            fence = not fence
            continue
        if fence or not line.strip() or re.fullmatch(r"[\s|:\-]+", line) or line.lstrip().startswith("#"):
            continue
        is_row = line.lstrip().startswith("|")
        if is_row and n < len(lines) and re.fullmatch(r"\s*\|?[\s|:\-]+\|?\s*", lines[n]) and "-" in lines[n]:
            continue   # a table header row (the next line is the separator) states no fact (auditor item 2)
        pieces = [line] if is_row or fname.lower().endswith(".csv") else split_sentences(line)
        cursor = 0
        for piece in pieces:
            off = line.find(piece, cursor)
            off = cursor if off < 0 else off
            cursor = off + len(piece)
            a, b = start + off, start + off + len(piece)
            inside = sum(max(0, min(b, y) - max(a, x)) for x, y in ranges)
            outside = re.sub(r"\[(?:[^\[\]]|\[[^\[\]]*\])*\]", " ", piece)
            labelled = bool(LINE_LABEL.search(outside)) or (inside >= 0.5 * max(1, b - a) and len(WORD.findall(outside)) < 3) or bool(re.search(r"\bVERIFY WITH\b", piece))
            if is_row and not LINE_LABEL.search(re.sub(r"\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]", " ", piece)) and not re.search(r"as pasted|search result|not opened|hypothetical|assumption", piece, re.I):
                # a row whose only label is a bracket slot in one cell: the other cells still state facts (auditor item 4)
                rest = [c for c in piece.strip().strip("|").split("|") if not re.fullmatch(r"\s*\[(?:[^\[\]]|\[[^\[\]]*\])*\]\s*", c)]
                if rest and len(rest) < len(piece.strip().strip("|").split("|")):
                    labelled = False
                    piece = "| " + " | ".join(c.strip() for c in rest) + " |"
            bare = strip_labels(piece)
            if res and res[-1][0] == fname and res[-1][1] == n and labelled and len(bare.split()) < 3 and not piece.lstrip("*_ ").startswith("["):
                res[-1] = (res[-1][0], res[-1][1], res[-1][2], True)   # a label standing alone labels the sentence before it
                continue
            res.append((fname, n, piece.strip(), labelled))
    return res


def strip_labels(s):
    s = re.sub(r"\[(?:draft for you to confirm|user to add|principal to confirm)[^:\]]*:?", " ", s, flags=re.I)
    s = LINE_LABEL.sub(" ", s)
    s = re.sub(r"[*_`#>|\[\]()\"]", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def uid(s):
    return hashlib.sha1(strip_labels(s).encode("utf-8")).hexdigest()[:6]


def flags(text, mid_caps):
    text = re.sub(r"`[^`]*`|https?://\S+|\]\([^)]*\)|(?:/[\w.\-]+){2,}", " ", text)   # code spans, links and paths are not claims
    f = []
    if FIG.search(re.sub(r"\b[A-Za-z]+\d+[A-Za-z]+\b|python3|^[\s*_-]*\d{1,2}[.)]\s", " ", text)):   # B2B, D2C and python3 are not figures (auditor item 10)
        f.append("FIG")
    words = WORD.findall(re.sub(r"\[Name\]", "", text))
    names = [w for i, w in enumerate(words) if (w[0].isupper() and w.strip("'.") not in COMMON and (i > 0 or w in mid_caps))]
    if not names and LEAD_NAME.match(text.strip("*_ #>|-")) and words and words[0] not in COMMON:
        names = words[:1]   # a sentence that opens with a name and a verb: "Gartner has a policy ...", "SHRM is US-based"
    if names:
        f.append("NAME")
    if YOU.search(text) or YOU_US.search(text):
        f.append("YOU")
    if SEAT.search(text):
        f.append("SEAT")
    if ABSENCE.search(re.sub(r"(?i)\byou (?:did|do) ?n[o']t \w+|\bha(?:s|ve) no (?:source|link|date)\b", " ", text)) and "python" not in text.lower() and not re.match(r"[\s*_-]*(?:do not|don't|never)\b", text, re.I):
        f.append("ABS")   # an instruction ("Do not say ...") or a python note is not an absence claim (auditor item 8)
    return f


def claim_units(files):
    allu = []
    for p in files:
        allu += units(read(p), os.path.basename(p))
    mid = set()
    for _, _, t, _ in allu:
        ws = WORD.findall(t)
        mid |= {w for w in ws[1:] if w[0].isupper() and w not in COMMON}
    claims = []
    for f, n, t, lab in allu:
        bare = t.strip("*_ ")
        if lab or bare.endswith("?") or re.match(r"(?i)if\b", bare):
            continue
        fl = flags(t, mid)
        if fl:
            claims.append((uid(t), f, n, t, fl))
    return allu, claims


def lost_labels(allu, chat_name):
    chat = [(strip_labels(t), t) for f, n, t, lab in allu if f == chat_name and lab]
    errs = []
    for f, n, t, lab in allu:
        if f == chat_name or lab:
            continue
        key = strip_labels(t)
        if len(key) < 12:
            continue
        for ck, ct in chat:
            if len(ck) < 12:
                continue
            if ck == key or (len(ck) >= 25 and ck in key) or (len(key) >= 25 and key in ck) or difflib.SequenceMatcher(None, ck, key).ratio() >= 0.9:
                errs.append(f"LABEL LOST {f}:{n}: the chat answer marks this line ({ct[:90]}) but the saved file prints it with no label: {t[:120]}")
                break
    return errs


def unchecked_saved(files):
    """A file the answer names (.md, .txt, .csv) that exists next to the answer or one folder up, and is not in the check, is reported."""
    given = {os.path.realpath(p) for p in files}
    base = os.path.dirname(os.path.abspath(files[0]))
    errs, seen = [], set()
    for name in re.findall(r"[\w./\\~-]+\.(?:md|txt|csv)\b", read(files[0])):
        for root in (base, os.path.dirname(base), os.getcwd()):
            cand = os.path.realpath(os.path.join(root, os.path.expanduser(name)))
            if os.path.isfile(cand) and cand not in given and "claim-ledger" not in cand.split(os.sep) and cand not in seen:
                seen.add(cand)
                errs.append(f"SAVED FILE NOT CHECKED {name}: the answer names this saved file; add it to the check so its labels and lines are checked")
                break
    # a file saved in the working folder (the folder that holds claim-ledger/) in the 3 hours before the answer was written is a deliverable too
    if os.path.basename(base) == "claim-ledger":
        work, t0 = os.path.dirname(base), os.path.getmtime(files[0])
        for name in sorted(os.listdir(work)):
            cand = os.path.realpath(os.path.join(work, name))
            if (name.lower().endswith((".md", ".txt", ".csv")) and os.path.isfile(cand) and cand not in given and cand not in seen
                    and os.path.getmtime(cand) >= t0 - 3 * 3600):
                seen.add(cand)
                errs.append(f"SAVED FILE NOT CHECKED {name}: it was saved in the working folder in this session; add it to the check (a file only for a script goes in claim-ledger/)")
    return errs


def norm_url(u):
    u = u.strip().strip("<>").split("#")[0].lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")


def stem(w):
    w = w.lower().strip("'.-")
    for suf, rep in (("ies", "y"), ("ing", ""), ("ed", ""), ("es", ""), ("s", "")):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: len(w) - len(suf)] + rep
    return w


def content(s):
    s = re.sub(r"^[\s*_-]*[A-Za-z][\w ]{0,30}:\s", " ", s)   # an asset label such as "Short bio:" is not the user's claim
    return {stem(w) for w in WORD.findall(strip_labels(s)) if len(w) >= 3 and w.lower() not in STOP}


def numbers(s):
    return {n.replace(",", "") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", s)}


def main(argv):
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    if len(argv) < 2 or argv[0] not in ("list", "check"):
        print(__doc__)
        return 2
    mode, rest = argv[0], argv[1:]
    opts = {"--ledger": [], "--opened": [], "--prompt": [], "--script-out": []}
    files, cur = [], None
    for a in rest:
        if a in opts:
            cur = a
        elif a.startswith("--"):
            print(f"bad input: unknown option {a}")
            return 2
        elif cur:
            opts[cur].append(a)
            if cur != "--script-out":
                cur = None
        else:
            files.append(a)
    if cur and cur != "--script-out" and not opts[cur]:
        print(f"bad input: {cur} needs a file")
        return 2
    if not files:
        print("bad input: give the chat answer file first, then each saved file")
        return 2
    for p in files + sum(opts.values(), []):
        if not os.path.isfile(p):
            print(f"bad input: no such file {p}")
            return 2
    if not read(files[0]).strip():
        print("bad input: the answer file is empty; write the answer you will deliver first")
        return 2
    allu, claims = claim_units(files)
    errs = lost_labels(allu, os.path.basename(files[0]))
    errs += unchecked_saved(files)
    print(f"CLAIM LEDGER {mode}: {len(files)} file(s), {len(allu)} lines read, {len(claims)} need a source")
    for c in claims:
        print(f"{c[0]}  [{','.join(c[4])}]  {c[1]}:{c[2]}  {c[3][:160]}")
    if mode == "list":
        for e in errs:
            print(e)
        print("Next: write the ledger (one line per id: <id> | user|page|script|notes|general|absence|self | detail), or turn a line into a"
              " label or a [User to add: ...] slot, then run check.")
        return 1 if errs else 0
    if not opts["--ledger"]:
        print("bad input: check needs --ledger")
        return 2
    opened = {}
    for p in opts["--opened"]:
        for line in read(p).splitlines():
            if line.strip() and not line.startswith("#"):
                url, _, chk = line.partition("|")
                words = [w.strip().lower() for w in re.sub(r"(?i)^\s*checked:\s*", "", chk).split(",") if w.strip()]
                opened.setdefault(norm_url(url), set()).update(words)
    prompt = "\n".join(read(p) for p in opts["--prompt"])
    psents = [content(s) for s in re.split(r"(?<=[.!?])\s+|\n+", prompt) if s.strip()]
    script_out = "\n".join(read(p) for p in opts["--script-out"])
    entries = {}
    for n, line in enumerate(read(opts["--ledger"][0]).splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = [x.strip() for x in line.split("|")]
        if len(parts) < 2:
            errs.append(f"LEDGER line {n}: needs <id> | <source> | <detail>")
            continue
        for i in re.split(r"[,\s]+", parts[0]):
            if i:
                if i in entries:
                    errs.append(f"DUPLICATE {i}: ledger lines {entries[i][2]} and {n} both give a source; keep one")
                entries[i] = (parts[1].lower(), parts[2:], n)
    by_id = {c[0]: c for c in claims}
    for i in entries:
        if i not in by_id:
            errs.append(f"STALE {i}: no line of the text has this id now (the text changed after the list, or the id is wrong); run list again")
    for i, (_, f, n, t, fl) in by_id.items():
        if i not in entries:
            errs.append(f"NO SOURCE {i} {f}:{n}: {t[:120]}")
            continue
        src, detail, ln = entries[i]
        where = f"{i} {f}:{n}"
        if "ABS" in fl and src != "absence":
            errs.append(f"ABSENCE {where}: an absence claim needs an absence entry naming the word and the pages checked for it")
            continue
        if src == "user":
            if not prompt:
                errs.append(f"BAD INPUT {where}: source user needs --prompt with the user's message")
                continue
            miss = numbers(t) - numbers(prompt)
            if miss:
                errs.append(f"USER FIGURE {where}: {', '.join(sorted(miss))} is not in the user's message")
            if re.search(r"\bnot\b|n't\b|\bnever\b|\bno\b", t, re.I) and not re.search(r"\bnot\b|n't\b|\bnever\b|\bno\b", prompt, re.I):
                errs.append(f"USER NEGATION {where}: the line says not or never and the user's message never does; use the user's words")
            cw = content(t)
            best = max((len(cw & ps) / max(1, len(cw)) for ps in psents), default=0)
            if cw and best < 0.75:
                errs.append(f"USER WORDS {where}: only {best:.0%} of this line's words (75% needed) are in any one sentence the user wrote; use the user's own words, or mark it [Draft for you to confirm: ...]")
        elif src == "page":
            urls = re.findall(r"\S+", " ".join(detail))
            if not urls:
                errs.append(f"PAGE {where}: name the opened page")
            for u in urls:
                if norm_url(u) not in opened:
                    errs.append(f"NOT OPENED {where}: {u} is not in the list of pages opened in this session; label the line or leave it out")
        elif src == "script":
            miss = numbers(t) - numbers(script_out)
            if not script_out:
                errs.append(f"BAD INPUT {where}: source script needs --script-out with the script's printed output")
            elif miss:
                errs.append(f"SCRIPT FIGURE {where}: {', '.join(sorted(miss))} is not in the script output; copy the script's figure and its meaning exactly")
        elif src == "notes":
            ref = (detail[0] if detail else "").strip()
            if not ref or not os.path.isfile(os.path.join(HERE, "..", "references", os.path.basename(ref))):
                errs.append(f"NOTES {where}: name a file in this skill's references folder")
            elif not (HEDGE.search(t) or re.search(r"\bnotes?\b", t, re.I)):
                errs.append(f"NOTES {where}: a general line from the sector notes is hedged (often, may, worth checking) or names the notes")
        elif src == "general":
            if "NAME" in fl or "YOU" in fl:
                errs.append(f"GENERAL {where}: names a company, a person or the user, so it is not general; give its source, label it, or leave it out")
            elif not HEDGE.search(t):
                errs.append(f"GENERAL {where}: a general claim about how people or companies behave needs hedged wording (often, may, worth checking)")
        elif src == "absence":
            if "ABS" not in fl:
                errs.append(f"ABSENCE {where}: the line states no absence")
                continue
            word = detail[0].strip().lower() if detail else ""
            urls = re.findall(r"\S+", " ".join(detail[1:]))
            if not word or not urls:
                errs.append(f"ABSENCE {where}: give the word and the pages: <id> | absence | <word> | <url> <url>")
                continue
            if word.lower() not in t.lower():
                errs.append(f"ABSENCE {where}: the word '{word}' is not in the line; the entry must name the word the line says is missing")
            for u in urls:
                if norm_url(u) not in opened:
                    errs.append(f"NOT OPENED {where}: {u} is not in the list of opened pages")
                elif word not in opened[norm_url(u)]:
                    errs.append(f"NOT CHECKED {where}: {u} was opened but not checked for '{word}'; name only the pages checked for it")
            if re.search(r"\banywhere\b|\bnowhere\b|whole site|entire site|across the site|the site does", t, re.I):
                errs.append(f"ABSENCE {where}: the line speaks for the whole site; name only the pages checked for '{word}'")
            if not re.search(r"pages? (?:I|we) (?:opened|checked|read)|https?://|\b[a-z0-9-]+\.(?:com|in|io|ai|org|co|net)\b", t, re.I):
                errs.append(f"ABSENCE {where}: the line must name the pages it checked (for example 'on the pages I opened: home, about')")
        elif src == "self":
            if not re.match(r"[*_\s-]*(?:I|I've|I'd|I'll|I'm)\b", t) or "YOU" in fl or "FIG" in fl and not re.search(r"\b(?:left out|kept out|removed|dropped|did not use|didn't use|counted|ran|checked)\b", t):
                errs.append(f"SELF {where}: source self is only for a line that says what this answer did (it starts with I), not a fact about anyone")
        elif src == "search":
            errs.append(f"SEARCH ONLY {where}: label it \"from a search result, page not opened\" in every place it appears, or leave it out")
        else:
            errs.append(f"LEDGER line {ln}: unknown source '{src}' (user, page, script, notes, general, absence, self)")
    for e in errs:
        print(e)
    if errs:
        print(f"LEDGER FAIL: {len(errs)} problem(s). Fix the text or the ledger, then run check again; deliver only text that passed.")
        return 1
    digest = hashlib.sha1("".join(read(p) for p in files).encode("utf-8")).hexdigest()[:10]
    print(f"LEDGER PASS: {len(claims)} line(s) traced, labels kept in every saved file. Checked text {digest}: deliver these files exactly as checked;"
          " any change after this needs a new check.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
