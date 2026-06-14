#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
WIKI = ROOT / "wiki"


PROMPT = """你是 Tina-巴菲特知识库的编译器。请把原文整理成结构化 Markdown Wiki 摘要。

要求：
1. 摘要长度约为原文 20-30%。
2. 使用 [[双向链接]] 关联巴菲特投资概念、公司和人物。
3. 输出结构必须包含：
# 标题
## 核心要点
## 详细摘要
## 提到的概念
## 提到的公司
## 提到的人物
## 原文金句
4. 不要输出 YAML frontmatter，脚本会自动添加。
"""


def category_for(path: Path) -> tuple[str, str]:
    rel = path.relative_to(RAW)
    if rel.parts[0] == "interviews":
        return "interviews", "interview-summary"
    if rel.parts[0] == "letters":
        return "letters", "letter-summary"
    raise ValueError(f"unsupported raw path: {path}")


def call_claude(text: str, title: str) -> str:
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise SystemExit("Please install anthropic: pip install anthropic") from exc
    client = Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        base_url=os.environ.get("ANTHROPIC_BASE_URL") or None,
    )
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    message = client.messages.create(
        model=model,
        max_tokens=6000,
        messages=[{"role": "user", "content": f"{PROMPT}\n\n标题：{title}\n\n原文：\n{text}"}],
    )
    return "".join(block.text for block in message.content if getattr(block, "type", "") == "text")


def clean_raw_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("> **Source**") or stripped.startswith("> **Type**"):
            continue
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


def local_summary(text: str, title: str) -> str:
    clean = clean_raw_text(text)
    plain = re.sub(r"```.*?```", "", clean, flags=re.S)
    plain = re.sub(r"#+\s*", "", plain)
    plain = re.sub(r"\s+", " ", plain).strip()
    excerpt = plain[:1800] if plain else "原文已导入，可在页面底部展开查看。"
    quote = plain[:160] if plain else "暂无可提取金句。"
    return f"""# {title}摘要

## 核心要点

- 本页面由本地模式生成，未调用外部 AI。
- 已保留原文路径，前端详情页可展开阅读完整原文。
- 后续如果接入 API，可以重新运行摄取脚本生成更精炼的结构化摘要。

## 详细摘要

{excerpt}

## 提到的概念

待补充

## 提到的公司

待补充

## 提到的人物

待补充

## 原文金句

{quote}
"""


def frontmatter(title: str, page_type: str, source: Path) -> str:
    today = date.today().isoformat()
    year_match = re.search(r"(19|20)\d{2}", title)
    page_date = f"{year_match.group(0)}-01-01" if year_match else today
    rel = source.relative_to(ROOT).as_posix()
    return f"""---
title: "{title}"
type: {page_type}
date: {page_date}
source: "{rel}"
tags: [{page_type}]
related: []
created: {today}
updated: {today}
---

"""


def ingest_file(path: Path, dry_run: bool, local: bool) -> None:
    category, page_type = category_for(path)
    title = path.stem
    output = WIKI / category / f"{title}摘要.md"
    print(f"{'DRY ' if dry_run else ''}ingest {path.relative_to(ROOT)} -> {output.relative_to(ROOT)}")
    if dry_run:
        return
    raw_text = path.read_text(encoding="utf-8")
    if local or not os.environ.get("ANTHROPIC_API_KEY"):
        body = local_summary(raw_text, title).strip() + "\n"
    else:
        body = call_claude(raw_text, title).strip() + "\n"
    output.write_text(frontmatter(title, page_type, path) + body, encoding="utf-8")
    with (WIKI / "log.md").open("a", encoding="utf-8") as log:
        log.write(f"\n- {date.today().isoformat()}：摄取 `{path.relative_to(ROOT).as_posix()}`。\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--local", action="store_true", help="不调用 API，直接把原文包装成基础 Wiki 摘要")
    args = parser.parse_args()
    if args.all:
        targets = sorted([*RAW.glob("interviews/*.md"), *RAW.glob("letters/**/*.md")])
    elif args.target:
        target = ROOT / args.target
        targets = sorted(target.rglob("*.md")) if target.is_dir() else [target]
    else:
        raise SystemExit("Use --all, a raw file, or a raw directory")
    targets = [target for target in targets if target.name.lower() != "summary.md"]
    for target in targets:
        ingest_file(target, args.dry_run, args.local)
    if not args.dry_run:
        subprocess.run(["python3", str(ROOT / "code" / "update_index.py")], check=False)


if __name__ == "__main__":
    main()
