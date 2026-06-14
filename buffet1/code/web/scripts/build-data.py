#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WIKI = ROOT / "wiki"
RAW = ROOT / "raw"
OUT = ROOT / "code" / "web" / "public" / "data"
PAGES = OUT / "pages"
CATEGORY_BY_DIR = {
    "concepts": "concepts",
    "companies": "companies",
    "people": "people",
    "interviews": "interviews",
    "letters": "letters",
    "insights": "insights",
}
TYPE_LABEL = {
    "concept": "核心概念",
    "company": "投资公司",
    "person": "关键人物",
    "interview-summary": "访谈与演讲",
    "letter-summary": "股东信",
    "insight": "交叉分析",
    "index": "索引",
}
LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip()
    body = text[end + 4 :].lstrip()
    data: dict[str, object] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [x.strip().strip('"').strip("'") for x in value[1:-1].split(",") if x.strip()]
            data[key] = items
        else:
            data[key] = value.strip('"').strip("'")
    return data, body


def summarize(body: str) -> str:
    text = re.sub(r"```.*?```", "", body, flags=re.S)
    text = re.sub(r"#+\s*", "", text)
    text = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:220]


def slug_for(path: Path) -> str:
    return path.stem


def category_for(path: Path) -> str:
    try:
        first = path.relative_to(WIKI).parts[0]
    except ValueError:
        return "index"
    return CATEGORY_BY_DIR.get(first, "index")


def copy_page(path: Path, rel: str) -> None:
    dest = PAGES / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def copy_raw() -> None:
    raw_out = OUT / "raw"
    if raw_out.exists():
        shutil.rmtree(raw_out)
    for name in ["letters", "interviews"]:
        src = RAW / name
        if src.exists():
            shutil.copytree(src, raw_out / name, dirs_exist_ok=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if PAGES.exists():
        shutil.rmtree(PAGES)
    PAGES.mkdir(parents=True, exist_ok=True)
    pages = []
    title_to_page = {}
    for path in sorted(WIKI.rglob("*.md")):
        if path.name in {"SCHEMA.md", "log.md"}:
            continue
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        rel = path.relative_to(WIKI).as_posix()
        title = str(fm.get("title") or path.stem)
        page_type = str(fm.get("type") or "index")
        category = category_for(path)
        links = sorted(set(LINK_RE.findall(body)))
        item = {
            "title": title,
            "type": page_type,
            "typeLabel": TYPE_LABEL.get(page_type, page_type),
            "date": fm.get("date", ""),
            "source": fm.get("source", ""),
            "tags": fm.get("tags", []),
            "related": fm.get("related", []),
            "path": rel,
            "markdownPath": f"/data/pages/{rel}",
            "category": category,
            "slug": slug_for(path),
            "summary": summarize(body),
            "links": links,
        }
        pages.append(item)
        title_to_page[title] = item
        copy_page(path, rel)
    nodes_by_title = {}
    edges = []
    for page in pages:
        nodes_by_title.setdefault(
            page["title"],
            {
                "id": page["title"],
                "title": page["title"],
                "type": page["type"],
                "category": page["category"],
                "slug": page["slug"],
                "path": page["path"],
            },
        )
        for link in page["links"]:
            target = title_to_page.get(link)
            if target:
                nodes_by_title.setdefault(
                    link,
                    {
                        "id": link,
                        "title": link,
                        "type": target["type"],
                        "category": target["category"],
                        "slug": target["slug"],
                        "path": target["path"],
                    },
                )
            else:
                nodes_by_title.setdefault(
                    link,
                    {"id": link, "title": link, "type": "unknown", "category": "unknown", "slug": link, "path": ""},
                )
            edges.append({"source": page["title"], "target": link})
    graph = {"nodes": list(nodes_by_title.values()), "edges": edges}
    search = [
        {
            "title": p["title"],
            "category": p["category"],
            "type": p["type"],
            "date": p["date"],
            "path": p["path"],
            "slug": p["slug"],
            "text": " ".join([p["title"], p["summary"], " ".join(p["links"]), " ".join(p.get("tags", []))]),
        }
        for p in pages
    ]
    (OUT / "wiki-index.json").write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "search-index.json").write_text(json.dumps(search, ensure_ascii=False, indent=2), encoding="utf-8")
    copy_raw()
    print(f"built {len(pages)} pages, {len(graph['nodes'])} nodes, {len(edges)} edges")


if __name__ == "__main__":
    main()

