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

  async function loadConversations() {
    loading.value = true
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
    } finally {
      loading.value = false
    }
  }

  async function addConversation() {
    const conversation = await createConversation({ title: '新建会话' })
    conversations.value = [conversation, ...conversations.value]
    await selectConversation(conversation.id)
    return conversation
  }

  async function renameConversation(conversationId, title) {
    const conversation = await updateConversation(conversationId, { title })
    conversations.value = conversations.value.map((item) =>
      item.id === conversation.id ? conversation : item,
    )
    return conversation
  }

  async function removeConversation(conversationId) {
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
    try {
      messages.value = await getMessages(conversationId)
    } finally {
      messagesLoading.value = false
    }
  }

  async function sendUserMessage(content) {
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
    streamError.value = ''

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
        appendAssistantChunk(assistantMessage.id, chunk)
      }

      const tail = decoder.decode()
      if (tail) {
        appendAssistantChunk(assistantMessage.id, tail)
      }

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
      if (error.name === 'AbortError') {
        return
      }

      streamError.value = error.message || 'DeepSeek stream failed'
      messages.value = messages.value.filter(
        (message) => message.id !== assistantMessage.id || message.content,
      )
      throw error
    } finally {
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
