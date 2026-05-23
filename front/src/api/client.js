const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return response.json()
  }
  return response.text()
}

function errorMessageFromBody(body, fallback) {
  if (body && typeof body === 'object') {
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail)) return body.detail.map((item) => item.msg || String(item)).join('; ')
    if (typeof body.message === 'string') return body.message
  }
  if (typeof body === 'string' && body.trim()) return body
  return fallback
}

export async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: options.body instanceof FormData
      ? options.headers
      : {
          'Content-Type': 'application/json',
          ...(options.headers || {}),
        },
  })
  const body = await parseResponse(response)
  if (!response.ok) {
    const message = errorMessageFromBody(body, `HTTP ${response.status}`)
    const error = new Error(message)
    error.status = response.status
    error.body = body
    throw error
  }
  return body
}

export function fileUrlFromReference(fileReference) {
  if (!fileReference?.path) return ''
  const path = fileReference.path.replace(/^\/+/, '')
  const match = path.match(/^workspace\/([^/]+)\/([^/]+)\/([^/]+)$/)
  if (!match) return ''
  const [, jobId, stage, filename] = match
  return `${API_BASE_URL}/files/${encodeURIComponent(jobId)}/${encodeURIComponent(stage)}/${encodeURIComponent(filename)}`
}

export function findFile(files = [], name) {
  return files.find((file) => file.name === name)
}

export function getTaskStatus(taskId) {
  return request(`/tasks/${encodeURIComponent(taskId)}`)
}

export function normalizeError(error) {
  if (!error) return '未知错误'
  return error.message || String(error)
}
