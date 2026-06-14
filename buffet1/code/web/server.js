import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import cors from "cors";
import express from "express";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(__dirname, "public", "data");
const port = Number(process.env.PORT || 3001);
const app = express();

app.use(cors());
app.use(express.json({ limit: "1mb" }));

let wikiIndex = [];
let graph = { nodes: [], edges: [] };
let neighbors = new Map();
let byTitle = new Map();

async function loadData() {
  wikiIndex = JSON.parse(await fs.readFile(path.join(dataDir, "wiki-index.json"), "utf-8"));
  graph = JSON.parse(await fs.readFile(path.join(dataDir, "graph.json"), "utf-8"));
  byTitle = new Map(wikiIndex.map((page) => [page.title, page]));
  neighbors = new Map();
  for (const edge of graph.edges) {
    const source = typeof edge.source === "object" ? edge.source.id : edge.source;
    const target = typeof edge.target === "object" ? edge.target.id : edge.target;
    if (!neighbors.has(source)) neighbors.set(source, new Set());
    if (!neighbors.has(target)) neighbors.set(target, new Set());
    neighbors.get(source).add(target);
    neighbors.get(target).add(source);
  }
}

function ngrams(input) {
  const clean = input.toLowerCase().replace(/\s+/g, " ").trim();
  const tokens = new Set(clean.split(" ").filter(Boolean));
  for (let size = 2; size <= 4; size += 1) {
    for (let i = 0; i <= clean.length - size; i += 1) {
      const token = clean.slice(i, i + size).trim();
      if (token.length === size) tokens.add(token);
    }
  }
  return [...tokens];
}

function scorePage(question, tokens, page) {
  const q = question.toLowerCase();
  const title = page.title.toLowerCase();
  const summary = (page.summary || "").toLowerCase();
  let score = 0;
  if (q.includes(title)) score += 50;
  if (title.includes(q) && q.length > 1) score += 40;
  for (const token of tokens) {
    if (title.includes(token)) score += 8;
    if (summary.includes(token)) score += 3;
  }
  for (const link of page.links || []) {
    if (q.includes(String(link).toLowerCase())) score += 6;
  }
  return score;
}

function retrieve(question) {
  const tokens = ngrams(question);
  const scored = wikiIndex
    .map((page) => ({ page, score: scorePage(question, tokens, page) }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score);
  const direct = scored.slice(0, 4);
  const chosen = new Map(direct.map((item) => [item.page.title, item]));
  for (const hit of direct) {
    for (const title of neighbors.get(hit.page.title) || []) {
      if (chosen.has(title) || !byTitle.has(title)) continue;
      const page = byTitle.get(title);
      const score = scorePage(question, tokens, page);
      if (score > 0) chosen.set(title, { page, score: score + 1 });
      if (chosen.size >= 6) break;
    }
    if (chosen.size >= 6) break;
  }
  return [...chosen.values()].sort((a, b) => b.score - a.score).map((item) => item.page);
}

async function pageText(page) {
  const fullPath = path.join(dataDir, "pages", page.path);
  const text = await fs.readFile(fullPath, "utf-8");
  return text.slice(0, 3000);
}

function sendSse(res, payload) {
  res.write(`data: ${JSON.stringify(payload)}\n\n`);
}

app.get("/", (req, res) => {
  res.type("html").send(`<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>AI Buffett API</title>
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; padding: 40px; line-height: 1.8; }
      code { background: #f2f2f2; padding: 2px 6px; border-radius: 6px; }
      a { color: #2563eb; }
    </style>
  </head>
  <body>
    <h1>AI 巴菲特后端已启动</h1>
    <p>这是 API 后端，不是网页前端。</p>
    <p>网页前端请打开：<code>http://localhost:5173</code></p>
    <p>测试搜索接口：<a href="/api/search?q=安全边际">/api/search?q=安全边际</a></p>
    <p>查看 OpenAPI：<a href="/openapi.yaml">/openapi.yaml</a></p>
  </body>
</html>`);
});

function publicPage(page) {
  return {
    title: page.title,
    type: page.type,
    typeLabel: page.typeLabel,
    category: page.category,
    date: page.date,
    summary: page.summary,
    links: page.links || [],
    tags: page.tags || [],
    path: page.path,
    url: `/page/${page.category}/${encodeURIComponent(page.slug)}`
  };
}

app.get("/api/search", (req, res) => {
  const query = String(req.query.q || "").trim();
  if (!query) {
    res.status(400).json({ error: "query parameter q is required" });
    return;
  }
  const results = retrieve(query).map(publicPage);
  res.json({ query, results });
});

app.get("/api/page", async (req, res) => {
  const title = String(req.query.title || "").trim();
  if (!title) {
    res.status(400).json({ error: "query parameter title is required" });
    return;
  }
  const page = byTitle.get(title);
  if (!page) {
    res.status(404).json({ error: "page not found", title });
    return;
  }
  const markdown = await pageText(page);
  res.json({ ...publicPage(page), markdown });
});

app.get("/openapi.yaml", (req, res) => {
  const protocol = req.get("x-forwarded-proto") || req.protocol;
  const host = req.get("host");
  res.type("yaml").send(`openapi: 3.1.0
info:
  title: AI Buffett Knowledge API
  version: 1.0.0
servers:
  - url: ${protocol}://${host}
paths:
  /api/search:
    get:
      operationId: searchKnowledge
      summary: 搜索 Tina-巴菲特知识库
      parameters:
        - name: q
          in: query
          required: true
          schema:
            type: string
          description: 用户的问题或搜索关键词
      responses:
        "200":
          description: 搜索结果
          content:
            application/json:
              schema:
                type: object
                properties:
                  query:
                    type: string
                  results:
                    type: array
                    items:
                      type: object
  /api/page:
    get:
      operationId: getKnowledgePage
      summary: 获取知识库页面 Markdown 全文
      parameters:
        - name: title
          in: query
          required: true
          schema:
            type: string
          description: 页面标题，例如 安全边际
      responses:
        "200":
          description: 页面内容
          content:
            application/json:
              schema:
                type: object
`);
});

app.post("/api/auth", (req, res) => {
  const password = process.env.ACCESS_PASSWORD || "";
  res.json({ ok: !password || req.body?.password === password, required: Boolean(password) });
});

app.post("/api/chat", async (req, res) => {
  const password = process.env.ACCESS_PASSWORD || "";
  if (password && req.body?.password !== password) {
    res.status(401).json({ error: "invalid password" });
    return;
  }
  const question = String(req.body?.message || "").trim();
  if (!question) {
    res.status(400).json({ error: "message required" });
    return;
  }
  res.setHeader("Content-Type", "text/event-stream; charset=utf-8");
  res.setHeader("Cache-Control", "no-cache, no-transform");
  res.setHeader("Connection", "keep-alive");
  const sources = retrieve(question);
  const context = (await Promise.all(sources.map(pageText)))
    .map((text, index) => `【资料 ${index + 1}: ${sources[index].title}】\n${text}`)
    .join("\n\n");
  if (!process.env.ANTHROPIC_API_KEY && !process.env.ANTHROPIC_AUTH_TOKEN) {
    const fallback = `当前没有配置大模型 API Key，所以我不能生成真正的 AI 回答。不过知识库检索正常。与你的问题最相关的页面是：${sources.map((s) => s.title).join("、") || "暂无命中"}。你可以点击这些页面阅读已编译内容和原文。`;
    sendSse(res, { text: fallback });
    sendSse(res, { done: true, sources: sources.map((s) => s.title) });
    res.end();
    return;
  }
  try {
    const { default: Anthropic } = await import("@anthropic-ai/sdk");
    const client = new Anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY || null,
      authToken: process.env.ANTHROPIC_AUTH_TOKEN || null,
      baseURL: process.env.ANTHROPIC_BASE_URL || undefined
    });
    const stream = client.messages.stream({
      model: process.env.ANTHROPIC_MODEL || "claude-sonnet-4-6",
      max_tokens: 1600,
      system: "你是 AI 巴菲特。用中文回答，风格理性、朴素、长期主义。只基于给定知识库上下文回答；若资料不足，明确说明。",
      messages: [
        {
          role: "user",
          content: `问题：${question}\n\n知识库上下文：\n${context}`
        }
      ]
    });
    for await (const event of stream) {
      if (event.type === "content_block_delta" && event.delta?.text) {
        sendSse(res, { text: event.delta.text });
      }
    }
    sendSse(res, { done: true, sources: sources.map((s) => s.title) });
    res.end();
  } catch (error) {
    sendSse(res, { error: error.message || "chat failed" });
    res.end();
  }
});

await loadData();
app.listen(port, () => {
  console.log(`AI Buffett server listening on http://localhost:${port}`);
});
