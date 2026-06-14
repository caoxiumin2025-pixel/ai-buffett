#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"


def split_long_line(line: str) -> list[str]:
    if len(line) <= 150 or line.strip().startswith(("#", "|", ">", "-", "*", "`")):
        return [line]
    parts = [p for p in re.split(r"(?<=。)", line) if p]
    if len(parts) <= 1:
        return [line]
    return [part.strip() for part in parts if part.strip()]


def fix_file(path: Path) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    changed = False
    for line in lines:
        parts = split_long_line(line)
        if len(parts) > 1:
            changed = True
            for part in parts:
                if out and out[-1].strip():
                    out.append("")
                out.append(part)
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

