---
name: agent-skills-search
description: Search and summarize skills from multiple directories (agent-skills.cc + skills.sh) using public sitemaps + page fetch (no APIs). Use when the user asks to find relevant agent skills, wants top N matches for keywords, or wants links + quick summaries (e.g., “top 8 skills for Laravel/Rust/DevOps/testing/security”).
---

# Agent Skills Search

Find relevant skills across:
- **https://agent-skills.cc**
- **https://skills.sh**

…and return a clean **Top 8** list with links and one-line summaries.

This skill avoids fragile client-side search scraping and avoids private APIs. Instead it uses:
- `https://agent-skills.cc/sitemap.xml` for discovery
- `https://skills.sh/sitemap.xml` for discovery
- fetching individual skill pages for details

## Quick workflow (Top 8, sitemap-first, multi-source)

1) **Get the query**
- Ask for 1–5 keywords.
- Default output size: **Top 8**.

2) **Discover candidate skill pages via sitemaps**
- Fetch both sitemaps:
  - `https://agent-skills.cc/sitemap.xml`
  - `https://skills.sh/sitemap.xml`
- Extract candidate URLs:
  - agent-skills.cc: `https://agent-skills.cc/skills/<slug>`
  - skills.sh: `https://skills.sh/<owner>/<repo>/<skill-slug>`
- Filter candidates by keyword match (case-insensitive) in the URL path first (fast).
  - If too few results, fetch some candidate pages and match against title/description too.

3) **Fetch details for the best candidates**
For each candidate skill page, extract (whatever is present):
- Title
- Short description
- Source/outbound link(s) (GitHub/docs)
- Popularity signals if visible (stars/likes/installs)
- Install hint if obvious
  - skills.sh often uses: `npx skills add <owner/repo>`

4) **Rank + dedupe (cross-source)**
- Remove duplicates:
  - Prefer dedupe by canonical GitHub `owner/repo` when you can extract it.
  - Fallback: title+description similarity.
- Prefer strong relevance:
  1) keyword match in title / slug
  2) match in description
  3) match in tags/category
  4) popularity as tiebreaker

5) **Return Top 8 in a consistent format**

- **1. <Skill title>** — <one-line why it matches>
  - Page: https://agent-skills.cc/skills/<slug>
  - Source: <GitHub/Other/Unknown>
  - Link(s): <GitHub/Docs/etc>

## Useful browsing URLs

Use these when the user wants discovery without a keyword query:

**agent-skills.cc**
- Home: https://agent-skills.cc/
- Claude skills: https://agent-skills.cc/claude-skills
- Codex skills: https://agent-skills.cc/codex-skills
- Cursor skills: https://agent-skills.cc/cursor-skills

**skills.sh**
- Home: https://skills.sh/
- Sitemap: https://skills.sh/sitemap.xml

## Bundled resources

### scripts/
- `scripts/search_skills.py`
  - End-to-end local search helper (both sources): sitemap discovery → fetch details → rank+dedupe → print Top N.
  - Example:
    - `python3 scripts/search_skills.py rag vector --limit 8 --fetch 40`
- `scripts/extract_skill_urls_from_sitemap.py`
  - Legacy helper (agent-skills.cc only).
- `scripts/extract_skill_urls_from_sitemaps.py`
  - Extract skill URLs from:
    - agent-skills.cc sitemap
    - skills.sh sitemap
  - Useful for quick local filtering and debugging.

### references/
If you need URL patterns and extraction guidance, read:
- `references/agent-skills-site-guide.md`
- `references/skills-sh-site-guide.md`
