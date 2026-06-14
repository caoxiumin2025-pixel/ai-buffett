#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"
KNOWN = {
    "概念解析",
    "定义与起源",
    "核心要义",
    "实践应用",
    "公司简介",
    "投资故事",
    "巴菲特评价精选",
    "人物简介",
    "核心要点",
    "详细摘要",
    "提到的概念",
    "提到的公司",
    "提到的人物",
    "原文金句",
}


def fix_file(path: Path) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    changed = False
    for line in lines:
        text = line.strip()
        if text in KNOWN:
            if out and out[-1].strip():
                out.append("")
            out.append(f"## {text}")
            changed = True
            continue
        out.append(line)
    if changed:
        path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    return changed


def main() -> None:
    changed = [p for p in WIKI.rglob("*.md") if fix_file(p)]
    print(f"fixed {len(changed)} files")


if __name__ == "__main__":
    main()

