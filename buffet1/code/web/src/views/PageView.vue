<script setup>
import MarkdownIt from "markdown-it";
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

const route = useRoute();
const md = new MarkdownIt({ html: false, linkify: true });
const pages = ref([]);
const page = ref(null);
const rendered = ref("");
const rawSource = ref("");

const colorByType = {
  concept: "var(--color-concept)",
  company: "var(--color-company)",
  person: "var(--color-person)",
  "interview-summary": "var(--color-interview)",
  "letter-summary": "var(--color-letter)"
};

const sourcePath = computed(() => {
  if (!page.value?.source) return "";
  return page.value.source.replace(/^raw\//, "/data/raw/");
});

function pageUrl(target) {
  return `/page/${target.category}/${encodeURIComponent(target.slug)}`;
}

function renderWikiLinks(text) {
  return text.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (_, title, alias) => {
    const target = pages.value.find((item) => item.title === title);
    const label = alias || title;
    return target ? `[${label}](${pageUrl(target)})` : label;
  });
}

function stripFrontmatter(text) {
  if (!text.startsWith("---")) return text;
  const end = text.find("\n---", 3);
  return end === -1 ? text : text.slice(end + 4).trimStart();
}

async function loadPage() {
  pages.value = await fetch("/data/wiki-index.json").then((res) => res.json());
  page.value = pages.value.find((item) => item.category === route.params.category && item.slug === route.params.slug);
  if (!page.value) return;
  const markdown = await fetch(page.value.markdownPath).then((res) => res.text());
  rendered.value = md.render(renderWikiLinks(stripFrontmatter(markdown)));
  rawSource.value = "";
  if (sourcePath.value && ["letters", "interviews"].includes(page.value.category)) {
    rawSource.value = await fetch(sourcePath.value)
      .then((res) => (res.ok ? res.text() : ""))
      .then((text) => text.split("\n").filter((line) => !line.trim().startsWith("> **Source**") && !line.trim().startsWith("> **Type**")).join("\n"));
  }
}

onMounted(loadPage);
watch(() => route.fullPath, loadPage);
</script>

<template>
  <div class="container" v-if="page">
    <div class="breadcrumbs">
      <RouterLink to="/">首页</RouterLink> / <RouterLink :to="`/category/${page.category}`">{{ page.typeLabel }}</RouterLink> / {{ page.title }}
    </div>
    <section class="hero">
      <div class="page-title">
        <span class="badge" :style="{ background: colorByType[page.type] || 'var(--accent)' }">{{ page.typeLabel }}</span>
        <h1>{{ page.title }}</h1>
        <p v-if="page.date">{{ page.date }}</p>
      </div>
    </section>
    <article class="card markdown" v-html="rendered"></article>
    <details v-if="rawSource" class="card source-toggle">
      <summary>📄 原文全文 — 展开阅读完整原文</summary>
      <div class="source-body">{{ rawSource }}</div>
    </details>
  </div>
  <div class="container" v-else>
    <div class="card panel">页面不存在</div>
  </div>
</template>

