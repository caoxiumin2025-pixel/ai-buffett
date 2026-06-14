---
title: "Wiki 结构规则"
type: index
date: 2026-06-13
source: ""
tags: [schema]
related: []
created: 2026-06-13
updated: 2026-06-13
---

# Wiki 结构规则

所有页面必须使用 Markdown，并包含 YAML frontmatter。

```yaml
---
title: "页面标题"
type: letter-summary | interview-summary | concept | company | person | insight | index
date: YYYY-MM-DD
source: "原始文件路径"
tags: [标签1, 标签2]
related: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

## 链接规则

- 使用 `[[双向链接]]` 关联实体。
- 每个实体必须有独立页面。
- 避免自链接。
- 摘要页应关联提到的概念、公司、人物和信件。

## 摘要页结构

# 标题

## 核心要点

## 详细摘要

## 提到的概念

## 提到的公司

## 提到的人物

## 原文金句

