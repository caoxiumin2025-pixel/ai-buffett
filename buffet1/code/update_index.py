#!/usr/bin/env python3
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"
CATEGORY_LABELS = {
    "concepts": "核心概念",
    "companies": "投资公司",
    "people": "关键人物",
    "interviews": "访谈与演讲",
    "letters": "股东信",
    "insights": "交叉分析",
}


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def title_for(path: Path) -> str:
    fm = parse_frontmatter(path.read_text(encoding="utf-8"))
    return fm.get("title") or path.stem


def main() -> None:
    today = date.today().isoformat()
    parts = [
        "---",
        'title: "全页面目录"',
        "type: index",
        f"date: {today}",
        'source: ""',
        "tags: [index]",
        "related: []",
        f"created: {today}",
        f"updated: {today}",
        "---",
        "",
        "# 全页面目录",
        "",
    ]
    for category, label in CATEGORY_LABELS.items():
        paths = sorted((WIKI / category).glob("*.md"))
        parts += [f"## {label}", "", "| 标题 | 路径 |", "| --- | --- |"]
        for path in paths:
            rel = path.relative_to(WIKI).as_posix()
            parts.append(f"| [[{title_for(path)}]] | `{rel}` |")
        parts.append("")
    (WIKI / "index.md").write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    print("updated wiki/index.md")


if __name__ == "__main__":
    main()

