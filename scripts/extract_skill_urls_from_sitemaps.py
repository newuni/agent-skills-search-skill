#!/usr/bin/env python3
"""Extract skill URLs from public sitemaps.

Supports:
- agent-skills.cc  (https://agent-skills.cc/sitemap.xml)
- skills.sh        (https://skills.sh/sitemap.xml)

Usage:
  python3 extract_skill_urls_from_sitemaps.py --source agent-skills
  python3 extract_skill_urls_from_sitemaps.py --source skills-sh

Filters:
  --contains <substring>   case-insensitive substring match on URL
  --limit <N>              limit output

Notes:
- No private API usage.
- This script is intentionally simple and robust.
"""

import argparse
import re
import sys
from urllib.request import Request, urlopen

SOURCES = {
    "agent-skills": {
        "sitemap": "https://agent-skills.cc/sitemap.xml",
        "pattern": r"https://agent-skills\.cc/skills/[^<\s]+",
    },
    "skills-sh": {
        "sitemap": "https://skills.sh/sitemap.xml",
        "pattern": r"https://skills\.sh/[^<\s]+",
    },
}


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": "clawdbot-agent-skills-search/1.1"})
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def dedupe_keep_order(urls):
    seen = set()
    out = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--source",
        choices=sorted(SOURCES.keys()),
        default="agent-skills",
        help="Which directory sitemap to use",
    )
    ap.add_argument("--sitemap", default=None, help="Override sitemap URL")
    ap.add_argument("--contains", default=None, help="case-insensitive substring filter on URL")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    src = SOURCES[args.source]
    sitemap_url = args.sitemap or src["sitemap"]

    xml = fetch(sitemap_url)

    urls = re.findall(src["pattern"], xml)
    urls = dedupe_keep_order(urls)

    if args.contains:
        needle = args.contains.lower()
        urls = [u for u in urls if needle in u.lower()]

    if args.limit and args.limit > 0:
        urls = urls[: args.limit]

    for u in urls:
        sys.stdout.write(u + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
