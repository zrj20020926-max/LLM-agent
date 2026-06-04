const baseURL = 'http://localhost:8000/api/v1'

export async function request(path, options = {}) {
  const response = await fetch(`${baseURL}${path}`, {
    headers: {
      'Content-Type': 'application/json', // // 告诉服务器发送的是 JSON 数据
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`)
  }

  return response.json()
}
