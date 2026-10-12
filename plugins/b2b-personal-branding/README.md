# B2B Personal Branding

Three skills for B2B professionals who want to be known for their work without inventing anything about themselves: founders, CXOs, marketing leaders, consultants and practitioners, and the ghostwriters and agencies who write for them.

## Skills

**personal-branding-authority** builds a positioning statement, short, medium, long and speaker bios with a host introduction, a LinkedIn headline and About section, a brand narrative, content pillars, and a 4 to 6 post personal branding series plan. Everything comes from a fact sheet of what you gave it; where your facts and the company's own pages support a line you did not write, it is offered as "[Draft for you to confirm: ...]" with its source, anything else missing is marked "[User to add: ...]", and your lived experience leads while credentials support.
Example prompt: "Here is my LinkedIn About and my CV. I lead product marketing for a service desk product. Give me positioning, a headline, and a short and a speaker bio."

**handcrafted-voice-audit** flags machine-sounding text line by line (dashes, banned words, stock openers, "That's not X. That's Y" lines, fragments, hyperbole, emoji, wrong weekdays), sets the reading level for your audience, and rewrites only what it flagged, keeping your raw take and any quotes from sources. It also builds a voice guide from a blank template and your own samples.
Example prompt: "Make this launch post sound human. Audience: contact center leaders."

**newsletter-creation-curation** plans a newsletter and writes each issue with three beats per story (what happened, why it matters, your take), subject lines, preview text, a separate share card and a teaser post. Every curated item carries its source link and a checked date, numbers are locked across every asset, and your platform's paste and render rules are checked before writing.
Example prompt: "Turn these three links and my notes into this fortnight's issue for heads of delivery."

## Install

In Claude Code:

```
/plugin marketplace add shashwatgtm/b2b-personal-branding
/plugin install b2b-personal-branding@b2b-personal-branding
```

## What it fetches and runs

The skills run inside Claude. When web search or fetch is available, they open only the pages needed: a company's own About page or press release, the pages you name, and your newsletter platform's help pages. They never search for or profile a person. Each skill has one small Python script (standard library only) with its own test file: the scripts count characters and words, find dashes, compare numbers across assets and check the weekday of written dates, and the voice audit's script also finds banned words and patterns. The scripts read only the text you give them, use no network, and write no files; --json only changes the printed format. Nothing is published, scheduled or sent by these skills.

## Examples

The worked examples in each skill use real companies (Freshworks, Happiest Minds and Observe.AI) only as examples, with every company fact quoted from a page fetched on 11 October 2026 and every figure about a person labelled hypothetical. No real employee of those companies is described.

## Privacy

This plugin sends no data to Helix GTM Consulting and runs no server. The plugin itself stores nothing: it keeps no account, no log and no copy of your work, and any file Claude writes for you goes only to your own working folder. When web tools are available, the skills open company pages, pages you name and your newsletter platform's help pages; they never search for or profile a person. What you type into Claude is handled under your own Claude account terms.

## Security

To report a security problem, email shashwat@gtmhelix.com with the subject "Security report: b2b-personal-branding". Please do not open a public issue for it.

## License

MIT. See LICENSE.
