import { request } from './request'

const baseURL = 'http://localhost:8000/api/v1'

export function getMessages(conversationId) {
  return request(`/conversations/${conversationId}/messages`)
}

export function createMessage(conversationId, payload) {
  return request(`/conversations/${conversationId}/messages`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function streamMessage(conversationId, messages, { signal } = {}) {
  const response = await fetch(`${baseURL}/conversations/${conversationId}/messages/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ messages }),
    signal,
  })

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`
    try {
      const payload = await response.json()
      detail = payload.detail || detail
    } catch {
      // Keep the status fallback when the error body is not JSON.
    }
    throw new Error(detail)
  }

  if (!response.body) {
    throw new Error('ReadableStream is not supported by this browser.')
  }

  return response.body.getReader()
}
