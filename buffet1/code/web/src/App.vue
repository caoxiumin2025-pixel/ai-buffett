<script setup>
import { computed, onMounted, ref } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";

const route = useRoute();
const pages = ref([]);

const counts = computed(() => {
  const map = { concepts: 0, companies: 0, people: 0, interviews: 0, letters: 0 };
  for (const page of pages.value) {
    if (map[page.category] !== undefined) map[page.category] += 1;
  }
  return map;
});

const nav = [
  { to: "/category/concepts", icon: "💡", label: "核心概念", count: "concepts" },
  { to: "/category/companies", icon: "🏢", label: "投资公司", count: "companies" },
  { to: "/category/people", icon: "👤", label: "关键人物", count: "people" },
  { to: "/category/interviews", icon: "🎤", label: "访谈与演讲", count: "interviews" },
  { to: "/category/letters", icon: "✉️", label: "股东信", count: "letters" }
];

onMounted(async () => {
  pages.value = await fetch("/data/wiki-index.json").then((res) => res.json());
});
</script>

<template>
  <aside class="sidebar">
    <RouterLink class="brand" to="/">📚 Tina-巴菲特知识库</RouterLink>
    <nav class="nav">
      <RouterLink class="nav-item" to="/">🏠 <span>知识库首页</span></RouterLink>
      <div class="nav-label">索引</div>
      <RouterLink v-for="item in nav.slice(0, 3)" :key="item.to" class="nav-item" :to="item.to">
        <span>{{ item.icon }}</span>
        <span>{{ item.label }}</span>
        <em>{{ counts[item.count] }}</em>
      </RouterLink>
      <div class="nav-label">来源</div>
      <RouterLink v-for="item in nav.slice(3)" :key="item.to" class="nav-item" :to="item.to">
        <span>{{ item.icon }}</span>
        <span>{{ item.label }}</span>
        <em>{{ counts[item.count] }}</em>
      </RouterLink>
      <div class="nav-label">工具</div>
      <RouterLink class="nav-item" to="/graph">🕸️ <span>知识图谱</span></RouterLink>
    </nav>
    <RouterLink class="ai-entry" :class="{ active: route.path === '/chat' }" to="/chat">
      <span>🧑‍💼 AI 巴菲特</span>
      <b>NEW</b>
    </RouterLink>
  </aside>
  <main class="main-shell">
    <RouterView />
  </main>
</template>

