#!/usr/bin/env python3
"""Extract https://agent-skills.cc/skills/<slug> URLs from the public sitemap.

Usage:
  python3 extract_skill_urls_from_sitemap.py > skills.txt
  python3 extract_skill_urls_from_sitemap.py --contains laravel --limit 50

Notes:
- No API usage. This relies only on sitemap.xml.
"""

import argparse
import re
import sys
from urllib.request import Request, urlopen

SITEMAP_URL = "https://agent-skills.cc/sitemap.xml"


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": "clawdbot-agent-skills-search/1.0"})
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sitemap", default=SITEMAP_URL)
    ap.add_argument("--contains", default=None, help="case-insensitive substring filter on URL")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    xml = fetch(args.sitemap)

    urls = re.findall(r"https://agent-skills\.cc/skills/[^<\s]+", xml)

    # de-dupe while keeping order
    seen = set()
    out = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)

    if args.contains:
        needle = args.contains.lower()
        out = [u for u in out if needle in u.lower()]

    if args.limit and args.limit > 0:
        out = out[: args.limit]

    for u in out:
        sys.stdout.write(u + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
