<script setup>
import * as d3 from "d3";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const graph = ref({ nodes: [], edges: [] });
const canvas = ref(null);

const colors = {
  concept: "#3B7DD8",
  company: "#47956A",
  person: "#C5961B",
  "interview-summary": "#7E5FAD",
  "letter-summary": "#C2604A",
  unknown: "#B9BDC8"
};

function draw() {
  const el = canvas.value;
  el.innerHTML = "";
  const width = el.clientWidth;
  const height = el.clientHeight;
  const nodes = graph.value.nodes.map((node) => ({ ...node }));
  const edges = graph.value.edges.map((edge) => ({ ...edge }));
  const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${width} ${height}`);
  const root = svg.append("g");
  svg.call(d3.zoom().scaleExtent([0.2, 5]).on("zoom", (event) => root.attr("transform", event.transform)));
  const sim = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(edges).id((d) => d.id).distance(58))
    .force("charge", d3.forceManyBody().strength(-90))
    .force("center", d3.forceCenter(width / 2, height / 2));
  const link = root.append("g").selectAll("line").data(edges).join("line").attr("stroke", "#E5E5EA").attr("stroke-width", 0.5);
  const node = root.append("g").selectAll("circle").data(nodes).join("circle")
    .attr("r", (d) => d.type === "unknown" ? 3 : 6)
    .attr("fill", (d) => colors[d.type] || colors.unknown)
    .attr("stroke", "#fff")
    .attr("stroke-width", 1.5)
    .style("cursor", (d) => d.path ? "pointer" : "default")
    .call(d3.drag()
      .on("start", (event) => {
        if (!event.active) sim.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      })
      .on("drag", (event) => {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      })
      .on("end", (event) => {
        if (!event.active) sim.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      }));
  node.on("click", (_, d) => {
    if (d.path) router.push(`/page/${d.category}/${encodeURIComponent(d.slug)}`);
  });
  const label = root.append("g").selectAll("text").data(nodes.filter((node) => node.type !== "unknown")).join("text")
    .text((d) => d.title)
    .attr("font-size", 9)
    .attr("fill", "#6B6B6B")
    .attr("dx", 8)
    .attr("dy", 3);
  sim.on("tick", () => {
    link.attr("x1", (d) => d.source.x).attr("y1", (d) => d.source.y).attr("x2", (d) => d.target.x).attr("y2", (d) => d.target.y);
    node.attr("cx", (d) => d.x).attr("cy", (d) => d.y);
    label.attr("x", (d) => d.x).attr("y", (d) => d.y);
  });
}

onMounted(async () => {
  graph.value = await fetch("/data/graph.json").then((res) => res.json());
  draw();
  window.addEventListener("resize", draw);
});
</script>

<template>
  <div class="container">
    <section class="hero">
      <div class="page-title">
        <h1>知识图谱</h1>
        <p>{{ graph.nodes.length }} 个节点 / {{ graph.edges.length }} 条连接</p>
        <div class="legend">
          <span><i style="background:#3B7DD8"></i>概念</span>
          <span><i style="background:#47956A"></i>公司</span>
          <span><i style="background:#C5961B"></i>人物</span>
          <span><i style="background:#7E5FAD"></i>访谈</span>
        </div>
      </div>
    </section>
    <section ref="canvas" class="card graph-card" style="margin-top:18px"></section>
  </div>
</template>

