<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

const route = useRoute();
const pages = ref([]);
const query = ref("");
const labels = {
  concepts: "核心概念",
  companies: "投资公司",
  people: "关键人物",
  interviews: "访谈与演讲",
  letters: "股东信",
  insights: "交叉分析"
};

const category = computed(() => route.params.type);
const title = computed(() => labels[category.value] || category.value);
const filtered = computed(() => {
  const term = query.value.trim().toLowerCase();
  return pages.value
    .filter((page) => page.category === category.value)
    .filter((page) => !term || `${page.title} ${page.summary}`.toLowerCase().includes(term))
    .sort((a, b) => String(b.date).localeCompare(String(a.date)));
});

function pageUrl(page) {
  return `/page/${page.category}/${encodeURIComponent(page.slug)}`;
}

onMounted(async () => {
  pages.value = await fetch("/data/wiki-index.json").then((res) => res.json());
});
watch(category, () => {
  query.value = "";
});
</script>

<template>
  <div class="container">
    <div class="breadcrumbs"><RouterLink to="/">首页</RouterLink> / {{ title }}</div>
    <section class="hero">
      <div class="page-title">
        <h1>{{ title }}</h1>
        <p>{{ filtered.length }} 个页面</p>
      </div>
    </section>
    <div class="search-box">
      <span>🔍</span>
      <input v-model="query" placeholder="按标题和摘要过滤" />
    </div>
    <section class="card">
      <RouterLink v-for="page in filtered" :key="page.path" class="list-row" :to="pageUrl(page)">
        <div>
          <strong>{{ page.title }}</strong>
          <div style="color:var(--text-secondary);font-size:13px;margin-top:5px">{{ page.summary }}</div>
        </div>
        <small>{{ page.date }}</small>
      </RouterLink>
    </section>
  </div>
</template>

