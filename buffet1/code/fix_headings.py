#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"


def looks_like_heading(line: str, prev_blank: bool) -> bool:
    text = line.strip()
    if not text or not prev_blank or text.startswith(("#", "-", "*", ">", "|", "`")):
        return False
    if len(text) > 25:
        return False
    body_markers = ("。", "，", "；", "：", ".", ",")
    return not any(marker in text for marker in body_markers)


def fix_file(path: Path) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    changed = False
    in_frontmatter = False
    fence_count = 0
    for i, line in enumerate(lines):
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
        elif in_frontmatter and line.strip() == "---":
            in_frontmatter = False
            out.append(line)
            continue
        if line.strip().startswith("```"):
            fence_count += 1
        prev_blank = not out or out[-1].strip() == ""
        if not in_frontmatter and fence_count % 2 == 0 and looks_like_heading(line, prev_blank):
            out.append(f"## {line.strip()}")
            changed = True
        else:
            out.append(line)
    if changed:
        path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    return changed


def main() -> None:
    changed = [p for p in WIKI.rglob("*.md") if fix_file(p)]
    print(f"fixed {len(changed)} files")


if __name__ == "__main__":
    main()

