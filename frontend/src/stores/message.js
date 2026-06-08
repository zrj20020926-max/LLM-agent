import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  createConversation,
  deleteConversation,
  getConversations,
  updateConversation,
} from '../api/conversations'
import { createMessage, getMessages, streamMessage } from '../api/message'

const CURRENT_CONVERSATION_KEY = 'agentdesk_current_conversation_id'

export const useMessageStore = defineStore('message', () => {
  const conversations = ref([])
  const currentConversationId = ref(null)
  const messages = ref([])
  const loading = ref(false)
  const messagesLoading = ref(false)
  const generating = ref(false)
  const streamError = ref('')
  let streamController = null

  const currentConversation = computed(
    () =>
      conversations.value.find(
        (conversation) => conversation.id === currentConversationId.value,
      ) || null,
  )

  function clearError() {
    streamError.value = ''
  }

  async function loadConversations() {
    loading.value = true
    clearError()
    try {
      conversations.value = await getConversations()
      const savedId = Number(localStorage.getItem(CURRENT_CONVERSATION_KEY))
      const savedConversation = conversations.value.find(
        (conversation) => conversation.id === savedId,
      )
      const nextConversation = savedConversation || conversations.value[0]

      if (nextConversation) {
        await selectConversation(nextConversation.id)
      } else {
        currentConversationId.value = null
        messages.value = []
        localStorage.removeItem(CURRENT_CONVERSATION_KEY)
      }
    } catch (error) {
      streamError.value = error.message || '会话加载失败'
      throw error
    } finally {
      loading.value = false
    }
  }

  async function addConversation() {
    clearError()
    const conversation = await createConversation({ title: '新建会话' })
    conversations.value = [conversation, ...conversations.value]
    await selectConversation(conversation.id)
    return conversation
  }

  async function renameConversation(conversationId, title) {
    clearError()
    const conversation = await updateConversation(conversationId, { title })
    conversations.value = conversations.value.map((item) =>
      item.id === conversation.id ? conversation : item,
    )
    return conversation
  }

  async function removeConversation(conversationId) {
    clearError()
    await deleteConversation(conversationId)
    conversations.value = conversations.value.filter(
      (conversation) => conversation.id !== conversationId,
    )

    if (currentConversationId.value === conversationId) {
      const nextConversation = conversations.value[0]
      if (nextConversation) {
        await selectConversation(nextConversation.id)
      } else {
        currentConversationId.value = null
        messages.value = []
        localStorage.removeItem(CURRENT_CONVERSATION_KEY)
      }
    }
  }

  async function selectConversation(conversationId) {
    clearError()
    currentConversationId.value = conversationId
    localStorage.setItem(CURRENT_CONVERSATION_KEY, String(conversationId))
    await loadMessages(conversationId)
  }

  async function loadMessages(conversationId = currentConversationId.value) {
    if (!conversationId) {
      messages.value = []
      return
    }

    messagesLoading.value = true
    clearError()
    try {
      messages.value = await getMessages(conversationId)
    } catch (error) {
      streamError.value = error.message || '消息加载失败'
      throw error
    } finally {
      messagesLoading.value = false
    }
  }

  async function sendUserMessage(content) {
    clearError()
    let conversationId = currentConversationId.value
    if (!conversationId) {
      const conversation = await addConversation()
      conversationId = conversation.id
    }

    const message = await createMessage(conversationId, {
      role: 'user',
      content,
    })
    messages.value = [...messages.value, message]
    await loadConversations()
    return message
  }

  async function sendMessageWithAssistantStream(content) {
    clearError()
    let conversationId = currentConversationId.value
    if (!conversationId) {
      const conversation = await addConversation()
      conversationId = conversation.id
    }

    const userMessage = await createMessage(conversationId, {
      role: 'user',
      content,
    })
    messages.value = [...messages.value, userMessage]

    const assistantMessage = {
      id: `stream-${Date.now()}`,
      conversation_id: conversationId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
    }
    messages.value = [...messages.value, assistantMessage]

    const requestMessages = messages.value
      .filter((message) => ['system', 'user', 'assistant'].includes(message.role))
      .filter((message) => message.content.trim().length > 0)
      .map((message) => ({
        role: message.role,
        content: message.content,
      }))

    streamController = new AbortController()
    generating.value = true
    // 定义一个临时字符串缓冲区。后端每次推过来的文本 chunk，不再立刻更新页面，而是先拼到这里。
    let chunkBuffer = ''
    // 记录当前是否已经安排了一次 requestAnimationFrame
    let frameId = null

    // 用来把 buffer 里的内容真正刷到 Vue 响应式状态里
    const flushBufferedChunks = () => {
      frameId = null
      if (!chunkBuffer) {
        return
      }

      const nextContent = chunkBuffer
      chunkBuffer = ''
      appendAssistantChunk(assistantMessage.id, nextContent)
    }

    const appendBufferedChunk = (chunk) => {
      if (!chunk) {
        return
      }

      chunkBuffer += chunk
      if (frameId === null) {
        frameId = requestAnimationFrame(flushBufferedChunks)
      }
    }

    const cancelPendingFlush = () => {
      if (frameId !== null) {
        cancelAnimationFrame(frameId)
        frameId = null
      }
    }

    try {
      const reader = await streamMessage(conversationId, requestMessages, {
        signal: streamController.signal,
      })
      const decoder = new TextDecoder()

      while (true) {
        const { value, done } = await reader.read()
        if (done) {
          break
        }

        const chunk = decoder.decode(value, { stream: true })
        appendBufferedChunk(chunk)
      }

      const tail = decoder.decode()
      if (tail) {
        appendBufferedChunk(tail)
      }
      cancelPendingFlush()
      flushBufferedChunks()

      const finalAssistantMessage = messages.value.find(
        (message) => message.id === assistantMessage.id,
      )
      if (finalAssistantMessage?.content.trim()) {
        const savedAssistantMessage = await createMessage(conversationId, {
          role: 'assistant',
          content: finalAssistantMessage.content,
        })
        messages.value = messages.value.map((message) =>
          message.id === assistantMessage.id ? savedAssistantMessage : message,
        )
      }

      await loadConversations()
    } catch (error) {
      cancelPendingFlush()
      flushBufferedChunks()
      if (error.name === 'AbortError') {
        return
      }

      streamError.value = error.message || 'AI 回复生成失败'
      messages.value = messages.value.filter(
        (message) => message.id !== assistantMessage.id || message.content,
      )
      throw error
    } finally {
      cancelPendingFlush()
      generating.value = false
      streamController = null
    }
  }

  function appendAssistantChunk(messageId, chunk) {
    messages.value = messages.value.map((message) =>
      message.id === messageId
        ? { ...message, content: `${message.content}${chunk}` }
        : message,
    )
  }

  function stopGenerating() {
    if (streamController) {
      streamController.abort()
    }
  }

  return {
    conversations,
    currentConversationId,
    currentConversation,
    messages,
    loading,
    messagesLoading,
    generating,
    streamError,
    clearError,
    loadConversations,
    addConversation,
    renameConversation,
    removeConversation,
    selectConversation,
    loadMessages,
    sendUserMessage,
    sendMessageWithAssistantStream,
    stopGenerating,
  }
})
