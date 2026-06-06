<template>
  <main class="chat-workspace">
    <aside class="session-sidebar">
      <div class="brand">AgentDesk</div>

      <el-button
        class="new-session-button"
        type="primary"
        plain
        :loading="chatStore.loading"
        @click="handleCreateConversation"
      >
        新建会话
      </el-button>

      <nav class="session-list" aria-label="会话列表">
        <button
          v-for="conversation in chatStore.conversations"
          :key="conversation.id"
          class="session-item"
          :class="{ active: conversation.id === chatStore.currentConversationId }"
          type="button"
          @click="chatStore.selectConversation(conversation.id)"
        >
          <span class="session-copy">
            <span class="session-title">{{ conversation.title }}</span>
            <span class="session-desc">{{ formatDate(conversation.updated_at) }}</span>
          </span>
          <span
            class="session-delete"
            role="button"
            tabindex="0"
            title="删除会话"
            @click.stop="handleDeleteConversation(conversation.id)"
            @keydown.enter.stop="handleDeleteConversation(conversation.id)"
          >
            ×
          </span>
        </button>

        <p v-if="!chatStore.loading && chatStore.conversations.length === 0" class="empty-hint">
          暂无会话
        </p>
      </nav>
    </aside>

    <section class="chat-main">
      <header class="assistant-header">
        <div>
          <h1>{{ chatStore.currentConversation?.title || 'LLM-Agent对话平台' }}</h1>
          <p>当前阶段仅保存用户消息，AI 回复将在下一阶段接入。</p>
        </div>
      </header>

      <div class="message-list">
        <p v-if="chatStore.messagesLoading" class="empty-hint">正在加载消息...</p>
        <p
          v-else-if="chatStore.currentConversationId && chatStore.messages.length === 0"
          class="empty-hint"
        >
          还没有消息
        </p>
        <p v-else-if="!chatStore.currentConversationId" class="empty-hint">
          点击“新建会话”开始聊天
        </p>

        <article
          v-for="message in chatStore.messages"
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
          @keydown.enter.exact.prevent="handleSend"
        />
        <el-button
          type="primary"
          :disabled="isSendDisabled"
          :loading="sending"
          @click="handleSend"
        >
          发送
        </el-button>
      </footer>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { useChatStore } from '../stores/chat'

const chatStore = useChatStore()
const inputText = ref('')
const sending = ref(false)

const isSendDisabled = computed(
  () => inputText.value.trim().length === 0 || sending.value,
)

function formatDate(value) {
  if (!value) {
    return ''
  }

  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

async function handleCreateConversation() {
  try {
    await chatStore.addConversation()
  } catch (error) {
    ElMessage.error('创建会话失败')
  }
}

async function handleDeleteConversation(conversationId) {
  if (!window.confirm('确定删除这个会话吗？')) {
    return
  }

  try {
    await chatStore.removeConversation(conversationId)
  } catch (error) {
    ElMessage.error('删除会话失败')
  }
}

async function handleSend() {
  const content = inputText.value.trim()
  if (!content || sending.value) {
    return
  }

  sending.value = true
  try {
    await chatStore.sendUserMessage(content)
    inputText.value = ''
  } catch (error) {
    ElMessage.error('发送失败')
  } finally {
    sending.value = false
  }
}

onMounted(async () => {
  try {
    await chatStore.loadConversations()
  } catch (error) {
    ElMessage.error('加载会话失败')
  }
})
</script>
