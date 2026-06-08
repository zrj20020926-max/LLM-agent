<template>
  <main class="message-workspace">
    <aside class="session-sidebar">
      <div class="brand">AgentDesk</div>

      <el-button
        class="new-session-button"
        type="primary"
        plain
        :loading="messageStore.loading"
        @click="handleCreateConversation"
      >
        新建会话
      </el-button>

      <nav class="session-list" aria-label="会话列表">
        <button
          v-for="conversation in messageStore.conversations"
          :key="conversation.id"
          class="session-item"
          :class="{ active: conversation.id === messageStore.currentConversationId }"
          type="button"
          @click="messageStore.selectConversation(conversation.id)"
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

        <p v-if="!messageStore.loading && messageStore.conversations.length === 0" class="empty-hint">
          暂无会话
        </p>
      </nav>
    </aside>

    <section class="message-main">
      <header class="assistant-header">
        <div>
          <h1>{{ messageStore.currentConversation?.title || 'LLM-Agent 对话平台' }}</h1>
          <p>当前阶段接入 DeepSeek 普通流式对话，不启用 tools、RAG 或 Agent 编排。</p>
        </div>
      </header>

      <div class="message-list">
        <p v-if="messageStore.messagesLoading" class="empty-hint">正在加载消息...</p>
        <p
          v-else-if="messageStore.currentConversationId && messageStore.messages.length === 0"
          class="empty-hint"
        >
          还没有消息
        </p>
        <p v-else-if="!messageStore.currentConversationId" class="empty-hint">
          点击“新建会话”开始聊天
        </p>

        <article
          v-for="message in messageStore.messages"
          :key="message.id"
          class="message-row"
          :class="message.role"
        >
          <div class="message-bubble markdown-bubble">
            <MessageContent :content="message.content" />
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
          v-if="!messageStore.generating"
          type="primary"
          :disabled="isSendDisabled"
          :loading="sending"
          @click="handleSend"
        >
          发送
        </el-button>
        <el-button v-else type="danger" plain @click="messageStore.stopGenerating">
          停止
        </el-button>
      </footer>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import MessageContent from '../components/chat/MessageContent.vue'
import { useMessageStore } from '../stores/message'

const messageStore = useMessageStore()
const inputText = ref('')
const sending = ref(false)

const isSendDisabled = computed(
  () => inputText.value.trim().length === 0 || sending.value || messageStore.generating,
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
    await messageStore.addConversation()
  } catch (error) {
    ElMessage.error('创建会话失败')
  }
}

async function handleDeleteConversation(conversationId) {
  if (!window.confirm('确定删除这个会话吗？')) {
    return
  }

  try {
    await messageStore.removeConversation(conversationId)
  } catch (error) {
    ElMessage.error('删除会话失败')
  }
}

async function handleSend() {
  const content = inputText.value.trim()
  if (!content || sending.value || messageStore.generating) {
    return
  }

  sending.value = true
  inputText.value = ''
  try {
    await messageStore.sendMessageWithAssistantStream(content)
  } catch (error) {
    ElMessage.error(error.message || '发送失败')
  } finally {
    sending.value = false
  }
}

onMounted(async () => {
  try {
    await messageStore.loadConversations()
  } catch (error) {
    ElMessage.error('加载会话失败')
  }
})
</script>
