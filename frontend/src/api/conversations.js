import { request } from './request'

export function getConversations() {
  return request('/conversations')
}

export function createConversation(payload = {}) {
  return request('/conversations', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateConversation(conversationId, payload) {
  return request(`/conversations/${conversationId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteConversation(conversationId) {
  return request(`/conversations/${conversationId}`, {
    method: 'DELETE',
  })
}
