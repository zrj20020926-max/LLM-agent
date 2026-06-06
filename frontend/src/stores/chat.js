import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  createConversation,
  deleteConversation,
  getConversations,
  updateConversation,
} from '../api/conversations'
import { createMessage, getMessages } from '../api/messages'

const CURRENT_CONVERSATION_KEY = 'agentdesk_current_conversation_id'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref([])
  const currentConversationId = ref(null)
  const messages = ref([])
  const loading = ref(false)
  const messagesLoading = ref(false)

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
    const conversation = await createConversation({ title: '新会话' })
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

  return {
    conversations,
    currentConversationId,
    currentConversation,
    messages,
    loading,
    messagesLoading,
    loadConversations,
    addConversation,
    renameConversation,
    removeConversation,
    selectConversation,
    loadMessages,
    sendUserMessage,
  }
})
