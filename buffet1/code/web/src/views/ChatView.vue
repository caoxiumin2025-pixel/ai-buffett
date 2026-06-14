<script setup>
import MarkdownIt from "markdown-it";
import { nextTick, onMounted, ref } from "vue";

const md = new MarkdownIt({ html: false, linkify: true });
const authRequired = ref(false);
const authed = ref(false);
const password = ref(sessionStorage.getItem("buffett-password") || "");
const error = ref("");
const input = ref("");
const loading = ref(false);
const messages = ref([]);
const examples = ["安全边际为什么重要？", "能力圈和风险控制有什么关系？", "巴菲特如何看待内在价值？"];

onMounted(async () => {
  try {
    const res = await fetch("/api/auth", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: "" })
    });
    const data = await res.json();
    authRequired.value = Boolean(data.required);
    authed.value = data.ok || (!data.required && sessionStorage.getItem("buffett-auth") !== "0");
  } catch {
    authRequired.value = false;
    authed.value = true;
  }
});

async function authenticate() {
  error.value = "";
  const res = await fetch("/api/auth", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password: password.value })
  });
  const data = await res.json();
  if (data.ok) {
    authed.value = true;
    sessionStorage.setItem("buffett-auth", "1");
    sessionStorage.setItem("buffett-password", password.value);
  } else {
    error.value = "密码不正确";
  }
}

function rendered(text) {
  return md.render(text || "");
}

async function ask(text = input.value) {
  const message = text.trim();
  if (!message || loading.value) return;
  input.value = "";
  messages.value.push({ role: "user", text: message });
  messages.value.push({ role: "assistant", text: "思考中..." });
  const index = messages.value.length - 1;
  loading.value = true;
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password: password.value, message })
  });
  if (!res.ok || !res.body) {
    messages.value[index] = { role: "assistant", text: "请求失败，请检查后端服务和访问密码。" };
    loading.value = false;
    return;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let textOut = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() || "";
    for (const chunk of chunks) {
      const line = chunk.split("\n").find((item) => item.startsWith("data: "));
      if (!line) continue;
      const payload = JSON.parse(line.slice(6));
      if (payload.text) {
        textOut += payload.text;
        messages.value[index] = { role: "assistant", text: textOut };
        await nextTick();
      }
      if (payload.done) {
        const sources = payload.sources?.length ? `\n\n资料来源：${payload.sources.join("、")}` : "";
        messages.value[index] = { role: "assistant", text: `${textOut}${sources}` };
      }
      if (payload.error) messages.value[index] = { role: "assistant", text: payload.error };
    }
  }
  loading.value = false;
}
</script>

<template>
  <div v-if="authRequired && !authed" class="auth-wrap">
    <form class="card auth-card" @submit.prevent="authenticate">
      <div style="font-size:38px">🔐</div>
      <h1>访问密码</h1>
      <input v-model="password" type="password" autocomplete="current-password" />
      <p class="error">{{ error }}</p>
      <button class="btn btn-blue" type="submit" style="width:100%">确认进入</button>
    </form>
  </div>
  <div v-else class="container chat-shell">
    <section class="hero">
      <div class="page-title">
        <h1>AI 巴菲特</h1>
        <p>基于已编译知识库的长期主义问答</p>
      </div>
    </section>
    <section class="card messages">
      <div v-if="!messages.length" class="empty-state">
        <div style="font-size:48px">🎩</div>
        <p>选择一个问题开始</p>
        <div class="examples">
          <button v-for="item in examples" :key="item" @click="ask(item)">{{ item }}</button>
        </div>
      </div>
      <div v-for="(message, idx) in messages" :key="idx" class="message" :class="message.role">
        <div class="msg-avatar">{{ message.role === "user" ? "👤" : "🎩" }}</div>
        <div class="bubble" v-html="rendered(message.text)"></div>
      </div>
    </section>
    <form class="card composer" @submit.prevent="ask()">
      <textarea v-model="input" placeholder="输入你的问题" @keydown.enter.exact.prevent="ask()"></textarea>
      <button class="btn btn-blue" :disabled="loading" type="submit">发送</button>
    </form>
  </div>
</template>
