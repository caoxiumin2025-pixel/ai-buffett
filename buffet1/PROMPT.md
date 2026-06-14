# Tina-巴菲特知识库

本项目基于 Andrej Karpathy 的 LLM Wiki 模式，构建一个巴菲特投资思想知识图谱网站。

核心理念：不做每次从零检索的传统 RAG，而是让 LLM 预编译知识成结构化 Wiki，查询时直接使用已编译好的知识回答。

## 模块

- `wiki/`：Markdown Wiki，使用 `[[双向链接]]`，兼容 Obsidian 图谱视图
- `code/web/`：Vue 3 前端、D3.js 知识图谱、全文搜索
- `code/web/server.js`：Express + Anthropic API 的 AI 巴菲特对话服务

## 常用命令

```bash
cd buffet1
python3 code/update_index.py
python3 code/web/scripts/build-data.py

cd code/web
npm install
node --env-file=.env server.js
npx vite --host
```
