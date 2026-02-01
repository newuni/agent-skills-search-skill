# Agent Skills (agent-skills.cc) — site guide

This skill intentionally avoids private/unstable `/api/*` usage.
Preferred strategy:
1) **Discover skill URLs from the public sitemap**
2) Fetch individual skill pages for details

## Core URL patterns

- Sitemap:
  - `https://agent-skills.cc/sitemap.xml`

- Skill detail pages:
  - `https://agent-skills.cc/skills/<slug>`
  - Slugs often look like: `owner-repo` or `OwnerRepo-repo`.

- Collection/browse pages:
  - Home: `https://agent-skills.cc/`
  - `https://agent-skills.cc/claude-skills`
  - `https://agent-skills.cc/codex-skills`
  - `https://agent-skills.cc/cursor-skills`

- Sort modes commonly exist:
  - `/top`, `/new`, `/hot` (e.g., `/claude-skills/top`)

## Discovery via sitemap

- Extract all URLs that match:
  - `https://agent-skills.cc/skills/<slug>`

- Filter by keywords using:
  - **slug substring match** first (fast)
  - then (if needed) fetch a larger shortlist and filter by **title/description**

## What to extract from a skill page

Try to capture these fields (whatever is present):
- **Title**
- **Short description**
- **Badges / Source** (e.g., GitHub)
- **Popularity signals** (stars/likes/forks — whatever the site shows)
- **Outbound link(s)** (GitHub repo is usually most useful)

## Ranking heuristics

When you have more than 8 candidates:
1) Exact keyword match in title
2) Strong match in description
3) Match in tags/category
4) Higher popularity metric (if visible)

## Output format

Keep the main answer compact:
- 8 numbered items
- 1 line description each
- always include the Agent Skills page link
- include GitHub link when available
