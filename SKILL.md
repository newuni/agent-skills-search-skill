---
name: agent-skills-search
description: Search and summarize skills from https://agent-skills.cc (Agent Skills marketplace) using the public sitemap + page fetch (no API). Use when the user asks to find relevant “agent skills” in that database/site, wants the top N matches for a query, or wants links + quick summaries (e.g., “top 8 skills for Laravel/Rust/DevOps/testing/security”).
---

# Agent Skills Search

Find relevant skills on **https://agent-skills.cc** and return a clean **Top 8** list with links and one-line summaries.

This skill avoids fragile client-side search scraping and avoids `/api/*`. Instead it uses:
- `https://agent-skills.cc/sitemap.xml` for discovery (stable)
- fetching each `/skills/<slug>` page for details

## Quick workflow (Top 8, sitemap-first)

1) **Get the query**
- Ask for 1–5 keywords.
- Default output size: **Top 8**.

2) **Discover candidate skill pages via sitemap**
- Fetch `https://agent-skills.cc/sitemap.xml`.
- Extract all URLs matching: `https://agent-skills.cc/skills/<slug>`.
- Filter candidates by keyword match (case-insensitive) in the **slug** first.
  - If too few results, fetch some candidate pages and match against title/description too.

3) **Fetch details for the best candidates**
For each candidate skill page, extract (whatever is present):
- Title (repo/skill name)
- Short description
- Source badge if visible (e.g., GitHub)
- Popularity signals if visible (stars/likes)
- Primary outbound link(s) (GitHub/docs)

4) **Rank + dedupe**
- Remove duplicates (same repo/slug).
- Prefer strong relevance:
  1) keyword match in title
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
- Home: https://agent-skills.cc/
- Claude skills: https://agent-skills.cc/claude-skills
- Codex skills: https://agent-skills.cc/codex-skills
- Cursor skills: https://agent-skills.cc/cursor-skills

## Bundled resources

### scripts/
- `scripts/extract_skill_urls_from_sitemap.py`
  - Extract `/skills/<slug>` URLs from the public sitemap.
  - Useful for quick local filtering and debugging.

### references/
If you need URL patterns and extraction guidance, read:
- `references/agent-skills-site-guide.md`
