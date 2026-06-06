import { request } from './request'

export function getMessages(conversationId) {
  return request(`/conversations/${conversationId}/messages`)
}

export function createMessage(conversationId, payload) {
  return request(`/conversations/${conversationId}/messages`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
