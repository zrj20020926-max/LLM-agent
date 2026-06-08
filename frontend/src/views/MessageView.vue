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

      <div class="message-panel">
        <div v-if="messageStore.streamError" class="message-error-banner">
          {{ messageStore.streamError }}
        </div>

        <div v-if="messageStore.messagesLoading" class="message-state">
          <el-skeleton :rows="4" animated />
          <p class="empty-hint">正在加载消息...</p>
        </div>
        <div
          v-else-if="messageStore.currentConversationId && messageStore.messages.length === 0"
          class="message-state"
        >
          <p class="empty-hint">还没有消息</p>
        </div>
        <div v-else-if="!messageStore.currentConversationId" class="message-state">
          <p class="empty-hint">点击“新建会话”开始聊天</p>
        </div>

        <DynamicScroller
          v-else
          ref="messageScroller"
          class="message-list"
          :items="messageStore.messages"
          key-field="id"
          :min-item-size="96"
          :buffer="520"
          @scroll.passive="handleMessageScroll"
        >
          <template #default="{ item, active }">
            <DynamicScrollerItem
              :item="item"
              :active="active"
              :size-dependencies="[item.content]"
            >
              <article class="message-row" :class="item.role">
                <div class="message-bubble markdown-bubble">
                  <span
                    v-if="isPendingAssistantMessage(item)"
                    class="typing-indicator"
                    aria-label="AI 正在生成"
                  >
                    <span></span>
                    <span></span>
                    <span></span>
                  </span>
                  <MessageContent v-else :content="item.content" />
                </div>
              </article>
            </DynamicScrollerItem>
          </template>
        </DynamicScroller>
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
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/index.css'

import MessageContent from '../components/chat/MessageContent.vue'
import { useMessageStore } from '../stores/message'

const messageStore = useMessageStore()
const inputText = ref('')
const sending = ref(false)
const messageScroller = ref(null)
const shouldStickToBottom = ref(true)

const isSendDisabled = computed(
  () => inputText.value.trim().length === 0 || sending.value || messageStore.generating,
)

const latestMessageContent = computed(() => {
  const latestMessage = messageStore.messages[messageStore.messages.length - 1]
  return latestMessage?.content || ''
})

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
    shouldStickToBottom.value = true
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
  shouldStickToBottom.value = true
  inputText.value = ''
  try {
    await messageStore.sendMessageWithAssistantStream(content)
  } catch (error) {
    ElMessage.error(error.message || '发送失败')
  } finally {
    sending.value = false
  }
}

function getScrollerElement() {
  const scroller = messageScroller.value
  if (!scroller) {
    return null
  }

  return scroller.$el || scroller.$?.subTree?.el || null
}

function isNearBottom(element) {
  if (!element) {
    return true
  }

  const distance = element.scrollHeight - element.scrollTop - element.clientHeight
  return distance < 96
}

function handleMessageScroll(event) {
  shouldStickToBottom.value = isNearBottom(event.target)
}

function isPendingAssistantMessage(message) {
  return (
    messageStore.generating &&
    message.role === 'assistant' &&
    String(message.id).startsWith('stream-') &&
    message.content.length === 0
  )
}

async function scrollToLatestMessage() {
  await nextTick()

  const lastIndex = messageStore.messages.length - 1
  if (lastIndex < 0 || !messageScroller.value) {
    return
  }

  messageScroller.value.scrollToItem(lastIndex)

  await nextTick()
  const element = getScrollerElement()
  if (element) {
    element.scrollTop = element.scrollHeight
  }
}

watch(
  () => messageStore.currentConversationId,
  async () => {
    shouldStickToBottom.value = true
    await scrollToLatestMessage()
  },
)

watch(
  () => messageStore.messages.length,
  async (newLength, oldLength) => {
    if (newLength > oldLength && shouldStickToBottom.value) {
      await scrollToLatestMessage()
    }
  },
)

watch(latestMessageContent, async () => {
  if (messageStore.generating && shouldStickToBottom.value) {
    await scrollToLatestMessage()
  }
})

watch(
  () => messageStore.messagesLoading,
  async (loading) => {
    if (!loading && shouldStickToBottom.value) {
      await scrollToLatestMessage()
    }
  },
)

onMounted(async () => {
  try {
    await messageStore.loadConversations()
    await scrollToLatestMessage()
  } catch (error) {
    ElMessage.error('加载会话失败')
  }
})
</script>
