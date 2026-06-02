<template>
  <main class="chat-workspace">
    <aside class="session-sidebar">
      <div class="brand">AgentDesk</div>

      <el-button class="new-session-button" type="primary" plain>
        新建会话
      </el-button>

      <nav class="session-list" aria-label="会话列表">
        <button
          v-for="session in sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: session.active }"
          type="button"
        >
          <span class="session-title">{{ session.title }}</span>
          <span class="session-desc">{{ session.desc }}</span>
        </button>
      </nav>
    </aside>

    <section class="chat-main">
      <header class="assistant-header">
        <div>
          <h1>前端学习助手</h1>
          <p>在线 · Vue3 / Vite / 前端工程化</p>
        </div>
      </header>

      <div class="message-list">
        <article
          v-for="message in messages"
          :key="message.id"
          class="message-row"
          :class="message.role"
        >
          <div class="message-bubble">
            {{ message.content }}
          </div>
        </article>
      </div>

      <footer class="composer">
        <el-input
          v-model="inputText"
          :autosize="{ minRows: 3, maxRows: 6 }"
          placeholder="输入你的问题..."
          resize="none"
          type="textarea"
        />
        <el-button type="primary" :disabled="isSendDisabled">
          发送
        </el-button>
      </footer>
    </section>
  </main>
</template>

<script setup>
import { computed, ref } from 'vue'

const inputText = ref('')

const sessions = [
  {
    id: 1,
    title: 'Vue3 入门计划',
    desc: '组件、响应式与组合式 API',
    active: true,
  },
  {
    id: 2,
    title: 'Vite 项目配置',
    desc: '路由、状态管理与构建',
    active: false,
  },
  {
    id: 3,
    title: 'Element Plus 布局',
    desc: '表单、按钮与工作台界面',
    active: false,
  },
]

const messages = [
  {
    id: 1,
    role: 'assistant',
    content: '你好，我是前端学习助手。你可以问我 Vue3、Vite、路由或组件设计相关的问题。',
  },
  {
    id: 2,
    role: 'user',
    content: '请帮我规划一个 Vue3 AI 聊天工作台的第一阶段页面。',
  },
]

const isSendDisabled = computed(() => inputText.value.trim().length === 0)
</script>
