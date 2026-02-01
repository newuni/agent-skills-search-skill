#!/usr/bin/env python3
"""Search skills across agent-skills.cc + skills.sh (sitemap-first).

This is a pragmatic, dependency-light search helper intended for:
- quick local runs
- debugging relevance/ranking
- producing a clean Top N list with links

It uses ONLY public sitemaps + page fetches (no private APIs).

Usage examples:
  python3 scripts/search_skills.py laravel docker
  python3 scripts/search_skills.py "rag" "vector" --limit 12
  python3 scripts/search_skills.py expo --source skills-sh
  python3 scripts/search_skills.py security --fetch 40 --limit 8

Notes:
- The web pages change; extraction is best-effort.
- To keep runs fast, we shortlist candidates by URL path match first,
  then fetch details for the top M candidates.
"""

from __future__ import annotations

import argparse
import dataclasses
import html
import re
import sys
import time
from typing import Iterable, List, Optional, Tuple

import requests

UA = "clawdbot-agent-skills-search/1.2 (+https://github.com/newuni/agent-skills-search-skill)"
TIMEOUT = 25

AGENT_SKILLS_SITEMAP = "https://agent-skills.cc/sitemap.xml"
SKILLS_SH_SITEMAP = "https://skills.sh/sitemap.xml"


@dataclasses.dataclass
class Skill:
    source: str  # agent-skills.cc | skills.sh
    page_url: str
    title: str = ""
    description: str = ""
    outbound_links: List[str] = dataclasses.field(default_factory=list)
    github_repo: str = ""  # owner/repo
    install_hint: str = ""
    score: float = 0.0


def _get(url: str) -> str:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def _dedupe_keep_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for it in items:
        if it in seen:
            continue
        seen.add(it)
        out.append(it)
    return out


def _extract_sitemap_urls(xml: str, source: str) -> List[str]:
    if source == "agent-skills.cc":
        urls = re.findall(r"https://agent-skills\.cc/skills/[^<\s]+", xml)
    elif source == "skills.sh":
        # skills.sh sitemap lists full detail URLs
        urls = re.findall(r"https://skills\.sh/[^<\s]+", xml)
        # avoid non-skill pages if they ever appear
        urls = [u for u in urls if u.count("/") >= 5]  # https://skills.sh/a/b/c
    else:
        raise ValueError(f"unknown source: {source}")
    return _dedupe_keep_order(urls)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _strip_tags(s: str) -> str:
    # very small HTML-to-text helper
    s = re.sub(r"<script[\s\S]*?</script>", " ", s, flags=re.I)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return _norm(s)


def _extract_title_description(page_html: str) -> Tuple[str, str]:
    # Prefer H1 for title
    h1 = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", page_html, flags=re.I)
    title = _strip_tags(h1.group(1)) if h1 else ""

    if not title:
        t = re.search(r"<title[^>]*>([\s\S]*?)</title>", page_html, flags=re.I)
        title = _strip_tags(t.group(1)) if t else ""
        title = re.sub(r"\s*\|\s*.*$", "", title)  # trim site suffix

    # Meta description is often decent
    md = re.search(
        r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"']([^\"']+)[\"']",
        page_html,
        flags=re.I,
    )
    desc = _norm(html.unescape(md.group(1))) if md else ""

    # If missing, take first non-trivial paragraph
    if not desc:
        paras = re.findall(r"<p[^>]*>([\s\S]*?)</p>", page_html, flags=re.I)
        for p in paras[:8]:
            text = _strip_tags(p)
            if len(text) >= 40:
                desc = text
                break

    return _norm(title), _norm(desc)


def _extract_outbound_links(page_html: str) -> List[str]:
    hrefs = re.findall(r"href=[\"']([^\"']+)[\"']", page_html, flags=re.I)
    out = []
    for h in hrefs:
        if h.startswith("/"):
            continue
        if h.startswith("#"):
            continue
        if h.startswith("mailto:"):
            continue
        # keep only plausible external links
        if h.startswith("http://") or h.startswith("https://"):
            out.append(h)
    # de-dupe
    return _dedupe_keep_order(out)


def _extract_github_repo(links: Iterable[str]) -> str:
    for l in links:
        m = re.search(r"https?://github\.com/([^/\s]+)/([^/\s#?]+)", l)
        if not m:
            continue
        owner, repo = m.group(1), m.group(2)
        # strip .git
        repo = re.sub(r"\.git$", "", repo)
        return f"{owner}/{repo}"
    return ""


def _skills_sh_owner_repo_from_url(url: str) -> str:
    # https://skills.sh/<owner>/<repo>/<slug>
    m = re.match(r"https?://skills\.sh/([^/]+)/([^/]+)/.+", url)
    if not m:
        return ""
    return f"{m.group(1)}/{m.group(2)}"


def _keyword_score(text: str, keywords: List[str]) -> float:
    t = text.lower()
    score = 0.0
    for kw in keywords:
        k = kw.lower()
        if not k:
            continue
        if k in t:
            # reward earlier hits a bit
            idx = t.find(k)
            score += 10.0
            score += max(0.0, 5.0 - min(5.0, idx / 40.0))
    return score


def _score_candidate(url: str, keywords: List[str]) -> float:
    path = url.lower()
    score = _keyword_score(path, keywords)
    # small bonus for more specific paths
    score += min(3.0, path.count("-") * 0.2)
    return score


def discover_candidates(keywords: List[str], source: str) -> List[Tuple[str, float]]:
    if source == "agent-skills.cc":
        xml = _get(AGENT_SKILLS_SITEMAP)
        urls = _extract_sitemap_urls(xml, "agent-skills.cc")
    elif source == "skills.sh":
        xml = _get(SKILLS_SH_SITEMAP)
        urls = _extract_sitemap_urls(xml, "skills.sh")
    else:
        raise ValueError(f"unknown source {source}")

    scored = [(u, _score_candidate(u, keywords)) for u in urls]
    scored.sort(key=lambda x: x[1], reverse=True)
    # If no keywords, just return head
    if not keywords:
        return scored
    # Keep only those with some match; fallback later if too few
    keep = [s for s in scored if s[1] > 0]
    return keep


def fetch_details(url: str, source: str) -> Skill:
    page = _get(url)
    title, desc = _extract_title_description(page)
    links = _extract_outbound_links(page)
    gh = _extract_github_repo(links)

    sk = Skill(source=source, page_url=url, title=title, description=desc, outbound_links=links, github_repo=gh)

    if source == "skills.sh":
        if not sk.github_repo:
            sk.github_repo = _skills_sh_owner_repo_from_url(url)
        if sk.github_repo:
            sk.install_hint = f"npx skills add {sk.github_repo}"

    return sk


def dedupe(skills: List[Skill]) -> List[Skill]:
    # Prefer de-dupe by github repo, else by page_url
    by_repo = {}
    out = []
    for s in skills:
        key = s.github_repo.lower() if s.github_repo else ""
        if key:
            if key in by_repo:
                # Keep the one with a description (or longer)
                prev = by_repo[key]
                if len(s.description) > len(prev.description):
                    by_repo[key] = s
                continue
            by_repo[key] = s
            out.append(s)
        else:
            out.append(s)

    # secondary de-dupe by URL
    uniq = []
    seen = set()
    for s in out:
        if s.page_url in seen:
            continue
        seen.add(s.page_url)
        uniq.append(s)
    return uniq


def rank(skills: List[Skill], keywords: List[str]) -> List[Skill]:
    for s in skills:
        s.score = 0.0
        s.score += 2.0 * _keyword_score(s.title, keywords)
        s.score += 1.2 * _keyword_score(s.description, keywords)
        s.score += 0.8 * _keyword_score(s.page_url, keywords)
        # Slight preference: if we found a GitHub repo, it's usually more useful
        if s.github_repo:
            s.score += 2.0
    skills.sort(key=lambda x: x.score, reverse=True)
    return skills


def render_markdown(skills: List[Skill], keywords: List[str], limit: int) -> str:
    kws = ", ".join(keywords) if keywords else "(no keywords)"
    lines = [f"Top {min(limit, len(skills))} results for: {kws}", ""]

    for i, s in enumerate(skills[:limit], 1):
        why = s.description or "(no description found)"
        why = why[:240] + ("…" if len(why) > 240 else "")

        lines.append(f"**{i}. {s.title or '(untitled)'}** — {why}")
        lines.append(f"- Source: {s.source}")
        lines.append(f"- Page: {s.page_url}")

        if s.github_repo:
            lines.append(f"- GitHub: https://github.com/{s.github_repo}")

        # show first 2 outbound links (excluding github if already shown)
        extra = []
        for l in s.outbound_links:
            if s.github_repo and ("github.com/" + s.github_repo).lower() in l.lower():
                continue
            if "skills.sh" in l or "agent-skills.cc" in l:
                continue
            extra.append(l)
            if len(extra) >= 2:
                break
        if extra:
            lines.append("- Links: " + ", ".join(extra))

        if s.install_hint:
            lines.append(f"- Install: `{s.install_hint}`")

        lines.append("")

    return "\n".join(lines).strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("keywords", nargs="*", help="1-5 keywords")
    ap.add_argument(
        "--source",
        choices=["agent-skills.cc", "skills.sh", "all"],
        default="all",
        help="which directory to search",
    )
    ap.add_argument("--limit", type=int, default=8, help="how many results to print")
    ap.add_argument(
        "--fetch",
        type=int,
        default=40,
        help="how many top URL-path candidates to fetch details for (per source)",
    )
    ap.add_argument("--sleep", type=float, default=0.0, help="sleep between fetches (seconds)")
    args = ap.parse_args()

    keywords = [k.strip() for k in args.keywords if k.strip()]
    if len(keywords) > 5:
        keywords = keywords[:5]

    sources = ["agent-skills.cc", "skills.sh"] if args.source == "all" else [args.source]

    all_skills: List[Skill] = []

    for src in sources:
        candidates = discover_candidates(keywords, src)
        # fallback: if keyword filter yields too few, take top anyway
        if len(candidates) < max(10, args.fetch // 2):
            # pull unfiltered head
            xml = _get(AGENT_SKILLS_SITEMAP if src == "agent-skills.cc" else SKILLS_SH_SITEMAP)
            urls = _extract_sitemap_urls(xml, src)
            candidates = [(u, _score_candidate(u, keywords)) for u in urls]
            candidates.sort(key=lambda x: x[1], reverse=True)

        shortlist = [u for (u, _s) in candidates[: max(1, args.fetch)]]

        for u in shortlist:
            try:
                sk = fetch_details(u, src)
                all_skills.append(sk)
            except Exception as e:
                # best-effort: keep going
                sys.stderr.write(f"[warn] {src} fetch failed: {u} ({e})\n")
            if args.sleep:
                time.sleep(args.sleep)

    all_skills = dedupe(all_skills)
    all_skills = rank(all_skills, keywords)

    sys.stdout.write(render_markdown(all_skills, keywords, args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
