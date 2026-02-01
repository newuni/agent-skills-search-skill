# Skills.sh — site guide

This skill treats **https://skills.sh/** as an additional skills directory/source.

Preferred strategy (same philosophy as agent-skills.cc):
1) **Discover skill URLs from the public sitemap**
2) Fetch individual skill pages for details

## Core URL patterns

- Sitemap:
  - `https://skills.sh/sitemap.xml`

- Skill detail pages (most common pattern observed in sitemap):
  - `https://skills.sh/<owner>/<repo>/<skill-slug>`

  Examples:
  - `https://skills.sh/anthropics/skills/skill-creator`
  - `https://skills.sh/vercel-labs/agent-skills/vercel-react-best-practices`

## Discovery via sitemap

- Extract all URLs in `<loc>`.
- Optionally filter by keywords using case-insensitive substring match on:
  - owner
  - repo
  - slug

## What to extract from a skill page

Try to capture (whatever is present):
- **Title** (H1)
- **Short description** (first paragraph/intro)
- **Outbound link(s)** (GitHub repo, docs)
- **Popularity signals** if visible (installs/likes/etc)

## Install hint

Skills.sh advertises a generic install command:
- `npx skills add <owner/repo>`

Note: this installs the repo package; the URL path may identify a specific skill/guide within that repo.
