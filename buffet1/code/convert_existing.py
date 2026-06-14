#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
WIKI = ROOT / "wiki"
CATEGORIES = {
    "concepts": "concept",
    "companies": "company",
    "people": "person",
}


def strip_existing_header(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---":
            continue
        if stripped.startswith("> **Source**") or stripped.startswith("> **Type**"):
            continue
        lines.append(line.rstrip())
    return "\n".join(lines).strip() + "\n"


def entity_names() -> list[str]:
    names: set[str] = set()
    for category in CATEGORIES:
        for path in (RAW / category).glob("*.md"):
            names.add(path.stem)
        for path in (WIKI / category).glob("*.md"):
            names.add(path.stem)
    return sorted(names, key=len, reverse=True)


def insert_wikilinks(text: str, names: list[str], self_name: str) -> str:
    in_code = False
    output = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            output.append(line)
            continue
        if in_code or stripped.startswith("#"):
            output.append(line)
            continue
        for name in names:
            if name == self_name or f"[[{name}]]" in line:
                continue
            pattern = re.compile(rf"(?<!\[\[){re.escape(name)}(?!\]\])")
            line = pattern.sub(f"[[{name}]]", line)
        output.append(line)
    return "\n".join(output).strip() + "\n"


def make_frontmatter(title: str, page_type: str, source: Path) -> str:
    today = date.today().isoformat()
    rel_source = source.relative_to(ROOT).as_posix()
    return f"""---
title: "{title}"
type: {page_type}
date: {today}
source: "{rel_source}"
tags: [{page_type}]
related: []
created: {today}
updated: {today}
---

"""


def convert(category: str, dry_run: bool) -> None:
    names = entity_names()
    src_dir = RAW / category
    dst_dir = WIKI / category
    dst_dir.mkdir(parents=True, exist_ok=True)
    for src in sorted(src_dir.glob("*.md")):
        title = src.stem
        body = strip_existing_header(src.read_text(encoding="utf-8"))
        body = insert_wikilinks(body, names, title)
        if not body.lstrip().startswith("#"):
            body = f"# {title}\n\n{body}"
        content = make_frontmatter(title, CATEGORIES[category], src) + body
        dst = dst_dir / src.name
        print(f"{'DRY ' if dry_run else ''}{src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
        if not dry_run:
            dst.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", choices=CATEGORIES.keys())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    for category in ([args.category] if args.category else CATEGORIES):
        convert(category, args.dry_run)


if __name__ == "__main__":
    main()

