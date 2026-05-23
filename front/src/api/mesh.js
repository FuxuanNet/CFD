import { request } from './client'

export function generateMesh(payload) {
  return request('/mesh/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function startMeshTask(payload) {
  return request('/mesh/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
