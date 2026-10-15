# B2B Personal Branding

Personal branding skills for B2B professionals, built by Shashwat Ghosh, Helix GTM Consulting.

- **personal-branding-authority**: positioning statement, short, medium, long and speaker bios, LinkedIn headline and About, brand narrative, content pillars, and a 4 to 6 post personal branding series plan, all built from your own facts with "[User to add: ...]" wherever a fact is missing.
- **handcrafted-voice-audit**: a line by line audit of machine-sounding text that rewrites only what it flags, keeps your raw take and source quotes, sets the reading level per audience, and builds a voice guide from a blank template.
- **newsletter-creation-curation**: newsletter plans and issues where every curated item cites its source link and a checked date, with subject lines, a separate share card and a teaser post, numbers locked across every asset.

Version 1.0.2. More plugins by Helix GTM Consulting: https://tools.gtmhelix.com/plugins/

## What changed in 1.0.2

- Newsletter: the issue check script no longer passes an issue with 0 curated items; it says "0 curated items found: each item must start with a '### ' heading". A deep dive issue (one topic, no curated items) is checked with the new --deep-dive option, and an empty issue never passes.
- Newsletter: the issue check script does not count a "### " line inside a code block as an item, reports a "### " heading with no title, counts the first item of a file saved with a byte order mark, and says it cannot read a missing file instead of stopping with an error.
- Newsletter: when your template marks items another way (for example bold lines), the check runs on a copy with "### " headings and your issue stays as it is; a mixed issue runs without --deep-dive, and the curation and distribution references say when to add it.
- Every script now writes UTF-8, so a rupee sign, a Unicode minus or a curly quote in your text no longer stops it with an encoding error on a Windows console or pipe set to code page 1252.
- Every command in the skills that says `python3` now also says to use `python` where `python3` is not found, as on Windows.
- Personal branding: two facts you gave are never joined into a claim you did not make (for example a topic you speak on); such a line is marked as a draft for you to confirm.
- Newsletter: a line about how your own team works is marked as a draft unless you said it; an item you gave that cannot be used gets a replacement offered as an option, not swapped in.
- The count script's --limit option now answers a value that is not a whole number of characters (for example "Short bio=50w"), or a field name that is not in the file, with a plain message, never a crash or a silent pass.

## What changed in 1.0.1

- When a pasted text, a file or a page the skill opens holds an instruction to the assistant, the answer now says so in one line at the top (where it was, what it asked, and that it was not followed). This step is part of each skill's delivery checklist.
- Bio and profile counts are given without the "[Draft for you to confirm: ...]" label words, so a target length is met on the text you will publish; the count script also says how many "[User to add: ...]" placeholders are still open.
- Every result on the fact sheet carries its employer, role and period; an acquisition, exit or result from after the person left an employer is never credited to them; a framework the person adapted from someone else's is credited in their own words.
- A writing sample sets a voice only when the person wrote it; a draft someone else wrote for them is not copied.
- A newsletter line about where a page's figures come from names the source the page gives for each figure.
- Revising an asset changes only what you asked; nothing from your earlier version is dropped without saying so, and your sources and citations are kept. Testimonials and recommendations are used only as you supply them, word for word. Links, handles and emails are only those you give; a profile is never attributed to you unless you confirm it.
- Your own framework is defined only from your own text or a source you name; your lead identity and focus order stay first in every asset; a fact you correct replaces the old value everywhere in the session; names you say must not appear are searched for in every asset before delivery; when a credential changes, the older assets that still carry it are listed for you.
- Paired short fields (a headline and an introduction) carry different information. Newsletters: a series across several issues or platforms gets an approved plan first, with each data point and story in one part only; you can pick the lead story from up to three candidates; the source table says which of your sources were used or left out, and why.
- Personal branding: a pillar angle or post opening that your facts do not cover gets a labelled draft topic from the company's opened pages wherever they support one, with your own moment left for you to add; the company is described only in the category words its own page uses. Voice audit: a fix never adds a cause or link between your claims that you did not make; "not just X. They are Y" and its variants are flagged by the script; every flag row names its line or sentence, and the answer itself uses no dashes.
- A company line you paste that no opened page shows, and that no opened page contradicts, is used and marked "as pasted, not yet checked" for you to confirm, instead of being dropped; a search hit on the company's own site or press release is opened first. Bios state the company's own category words plainly (no "describes itself as"), leave out its praise words and figures unless you ask, and use your sector's own words for your work.

## Install

```bash
# Add this repository as a marketplace
claude plugin marketplace add shashwatgtm/b2b-personal-branding

# Install the plugin
claude plugin install b2b-personal-branding@b2b-personal-branding
```

## Quick start

"Here is my CV and LinkedIn About. Write my positioning, a headline, and a speaker bio for a panel on agentic AI in delivery."

"Make this launch post sound human. Audience: contact center leaders."

"Turn these three links and my notes into this fortnight's newsletter issue for heads of delivery, with three subject lines and a share card."

## Examples

The worked examples inside the skills use real companies (Freshworks, Happiest Minds and Observe.AI) only as examples, with every company fact taken from a page fetched on 11 October 2026 and every figure a user supplies labelled hypothetical. No real employee of those companies is described.

## Privacy

This plugin sends no data to Helix GTM Consulting and runs no server. The plugin itself stores nothing: it keeps no account, no log and no copy of your work, and any file Claude writes for you goes only to your own working folder. The skills run inside Claude. When web tools are available, they open company pages, pages you name and your newsletter platform's help pages; they never search for or profile a person. The small Python scripts in each skill run on text you give them, use no network, and write no files. What you type into Claude is handled under your own Claude account terms.

## Security

To report a security problem, email shashwat@gtmhelix.com with the subject "Security report: b2b-personal-branding". Please do not open a public issue for it.

## License

MIT. See [LICENSE](LICENSE).
