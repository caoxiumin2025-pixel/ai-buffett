<script setup>
import * as d3 from "d3";
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

const pages = ref([]);
const graph = ref({ nodes: [], edges: [] });
const query = ref("");
const miniGraph = ref(null);

const counts = computed(() => {
  const map = { letters: 0, concepts: 0, companies: 0, interviews: 0 };
  for (const page of pages.value) {
    if (map[page.category] !== undefined) map[page.category] += 1;
  }
  return map;
});

const linkCounts = computed(() => {
  const counts = new Map();
  for (const edge of graph.value.edges) {
    const target = typeof edge.target === "object" ? edge.target.id : edge.target;
    counts.set(target, (counts.get(target) || 0) + 1);
  }
  return counts;
});

const topConcepts = computed(() => topByCategory("concepts"));
const topCompanies = computed(() => topByCategory("companies"));
const people = computed(() => pages.value.filter((page) => page.category === "people"));
const timeline = computed(() => pages.value.filter((page) => ["letters", "interviews"].includes(page.category) && page.date));
const searchResults = computed(() => {
  const term = query.value.trim().toLowerCase();
  if (!term) return [];
  return pages.value
    .filter((page) => `${page.title} ${page.summary}`.toLowerCase().includes(term))
    .slice(0, 8);
});

function topByCategory(category) {
  return pages.value
    .filter((page) => page.category === category)
    .map((page) => ({ ...page, count: linkCounts.value.get(page.title) || 0 }))
    .sort((a, b) => b.count - a.count || a.title.localeCompare(b.title, "zh-CN"))
    .slice(0, 15);
}

function pageUrl(page) {
  return `/page/${page.category}/${encodeURIComponent(page.slug)}`;
}

function dotStyle(page) {
  const year = Number(String(page.date).slice(0, 4));
  const pct = Math.max(0, Math.min(100, ((year - 1956) / (2025 - 1956)) * 100));
  const colors = {
    letters: page.source?.includes("partnership") ? "#3B7DD8" : "#47956A",
    interviews: "#7E5FAD"
  };
  return { left: `${pct}%`, "--dot": colors[page.category] || "#C5961B" };
}

function drawMiniGraph() {
  const el = miniGraph.value;
  if (!el) return;
  el.innerHTML = "";
  const width = 240;
  const height = 150;
  const nodes = graph.value.nodes.slice(0, 22).map((node) => ({ ...node }));
  const nodeIds = new Set(nodes.map((node) => node.id));
  const edges = graph.value.edges
    .filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target))
    .slice(0, 32)
    .map((edge) => ({ ...edge }));
  const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${width} ${height}`);
  const color = d3.scaleOrdinal().domain(["concept", "company", "person", "interview-summary", "letter-summary"]).range(["#6EA8FF", "#6CCB92", "#E1B847", "#A98BE0", "#D77E69"]);
  const sim = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(edges).id((d) => d.id).distance(34))
    .force("charge", d3.forceManyBody().strength(-42))
    .force("center", d3.forceCenter(width / 2, height / 2));
  const link = svg.append("g").selectAll("line").data(edges).join("line").attr("stroke", "rgba(255,255,255,0.28)");
  const node = svg.append("g").selectAll("circle").data(nodes).join("circle").attr("r", 5).attr("fill", (d) => color(d.type));
  sim.on("tick", () => {
    link.attr("x1", (d) => d.source.x).attr("y1", (d) => d.source.y).attr("x2", (d) => d.target.x).attr("y2", (d) => d.target.y);
    node.attr("cx", (d) => d.x).attr("cy", (d) => d.y);
  });
  setTimeout(() => sim.stop(), 4000);
}

onMounted(async () => {
  [pages.value, graph.value] = await Promise.all([
    fetch("/data/wiki-index.json").then((res) => res.json()),
    fetch("/data/graph.json").then((res) => res.json())
  ]);
  drawMiniGraph();
});
</script>

<template>
  <div class="container">
    <section class="hero">
      <div class="hero-inner">
        <div>
          <h1>Tina-巴菲特知识库</h1>
          <p>预编译的巴菲特投资思想 Wiki，连接信件、访谈、概念、公司与人物。</p>
          <div class="actions">
            <RouterLink class="btn btn-gold" to="/chat">🧑‍💼 问 AI 巴菲特</RouterLink>
            <RouterLink class="btn btn-ghost" to="/graph">🕸️ 探索知识图谱</RouterLink>
          </div>
        </div>
        <div ref="miniGraph" aria-label="迷你知识图谱"></div>
      </div>
    </section>

    <section class="stats-grid">
      <RouterLink class="card stat-card" style="--bar: var(--color-letter)" to="/category/letters">
        <div class="stat-top"><span>✉️</span><b>{{ counts.letters }}</b></div>
        <div class="stat-label">股东信</div>
      </RouterLink>
      <RouterLink class="card stat-card" style="--bar: var(--color-concept)" to="/category/concepts">
        <div class="stat-top"><span>💡</span><b>{{ counts.concepts }}</b></div>
        <div class="stat-label">核心概念</div>
      </RouterLink>
      <RouterLink class="card stat-card" style="--bar: var(--color-company)" to="/category/companies">
        <div class="stat-top"><span>🏢</span><b>{{ counts.companies }}</b></div>
        <div class="stat-label">投资公司</div>
      </RouterLink>
      <RouterLink class="card stat-card" style="--bar: var(--color-interview)" to="/category/interviews">
        <div class="stat-top"><span>🎤</span><b>{{ counts.interviews }}</b></div>
        <div class="stat-label">访谈与演讲</div>
      </RouterLink>
    </section>

    <div class="search-box">
      <span>🔍</span>
      <input v-model="query" placeholder="搜索知识库" />
    </div>
    <div v-if="searchResults.length" class="card">
      <RouterLink v-for="page in searchResults" :key="page.path" class="list-row" :to="pageUrl(page)">
        <strong>{{ page.title }}</strong>
        <small>{{ page.typeLabel }}</small>
      </RouterLink>
    </div>

    <section class="section-band band-concept">
      <div class="section-head">
        <h2 style="color:#8B6914">核心投资概念</h2>
        <small>TOP 15</small>
      </div>
      <div class="chip-wrap">
        <RouterLink v-for="page in topConcepts" :key="page.path" class="chip" :to="pageUrl(page)">
          {{ page.title }} <b style="background:#B8922A">{{ page.count }}</b>
        </RouterLink>
      </div>
    </section>

    <section class="section-band band-company">
      <div class="section-head">
        <h2 style="color:#3D7A52">重要公司</h2>
        <small>TOP 15</small>
      </div>
      <div class="chip-wrap">
        <RouterLink v-for="page in topCompanies" :key="page.path" class="chip" :to="pageUrl(page)">
          {{ page.title }} <b style="background:#47956A">{{ page.count }}</b>
        </RouterLink>
      </div>
    </section>

    <div class="content-grid">
      <section class="card panel">
        <div class="section-head"><h2>关键人物</h2></div>
        <div class="people-grid">
          <RouterLink v-for="page in people" :key="page.path" class="person-card" :to="pageUrl(page)">
            <div class="avatar">{{ page.title.slice(0, 1) }}</div>
            <div class="person-name">{{ page.title }}</div>
            <div class="person-count">{{ linkCounts.get(page.title) || 0 }} 次引用</div>
          </RouterLink>
        </div>
      </section>
      <section class="card panel">
        <div class="section-head"><h2>时间线</h2></div>
        <div class="timeline">
          <RouterLink v-for="page in timeline" :key="page.path" class="time-dot" :style="dotStyle(page)" :to="pageUrl(page)" :title="page.title" />
        </div>
        <div class="legend">
          <span><i style="background:#3B7DD8"></i>合伙人信</span>
          <span><i style="background:#47956A"></i>伯克希尔股东信</span>
          <span><i style="background:#7E5FAD"></i>访谈</span>
          <span><i style="background:#C5961B"></i>特别信件</span>
        </div>
      </section>
    </div>

    <section class="card panel" style="margin-top:18px">
      <div class="section-head"><h2>快速导航</h2></div>
      <div class="quick-grid">
        <RouterLink to="/category/concepts">💡 核心概念</RouterLink>
        <RouterLink to="/category/companies">🏢 投资公司</RouterLink>
        <RouterLink to="/category/people">👤 关键人物</RouterLink>
        <RouterLink to="/category/interviews">🎤 访谈与演讲</RouterLink>
        <RouterLink to="/category/letters">✉️ 股东信</RouterLink>
        <RouterLink to="/graph">🕸️ 知识图谱</RouterLink>
      </div>
    </section>
  </div>
</template>

