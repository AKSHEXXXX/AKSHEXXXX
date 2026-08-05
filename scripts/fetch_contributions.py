#!/usr/bin/env python3
"""Fetch the last ~53 weeks of GitHub contributions for a user.

Uses only the Python standard library. Works in GitHub Actions (via
GITHUB_TOKEN + GITHUB_ACTOR) or locally (set GH_USER or type a username
when prompted). Writes contributions.json, keyed by YYYY-MM-DD.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

USERNAME = (
    os.environ.get("GITHUB_ACTOR", "").strip()
    or os.environ.get("GH_USER", "").strip()
)
if not USERNAME:
    USERNAME = input("GitHub username: ").strip()
if not USERNAME:
    sys.exit("No username provided")


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "contribution-heatmap/1.0"},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read().decode("utf-8")


def main() -> None:
    url = f"https://github.com/users/{urllib.parse.quote(USERNAME)}/contributions"
    html = fetch(url)

    contributions: dict[str, int] = {}
    cell_pattern = re.compile(r'<td[^>]*>')
    for cell in cell_pattern.finditer(html):
        tag = cell.group(0)
        date_match = re.search(r'data-date="(\d{4}-\d{2}-\d{2})"', tag)
        if not date_match:
            continue
        count_match = re.search(r'data-count="(\d+)"', tag)
        if count_match:
            contributions[date_match.group(1)] = int(count_match.group(1))
        else:
            level_match = re.search(r'data-level="(\d+)"', tag)
            level = int(level_match.group(1)) if level_match else 0
            contributions[date_match.group(1)] = {0: 0, 1: 1, 2: 4, 3: 7, 4: 10}[level]

    if not contributions:
        sys.exit(
            "Could not parse contributions for " + USERNAME
            + ". Check the username, or the profile may be private."
        )

    out = os.environ.get("CONTRIB_JSON", "contributions.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(contributions, fh, indent=2, sort_keys=True)
    print(f"Saved {len(contributions)} days to {out}")


if __name__ == "__main__":
    main()