import { request } from './client'

export function listProjects() {
  return request('/projects')
}

export function createProject(payload) {
  return request('/projects', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateProject(projectId, payload) {
  return request(`/projects/${encodeURIComponent(projectId)}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteProject(projectId) {
  return request(`/projects/${encodeURIComponent(projectId)}`, {
    method: 'DELETE',
  })
}

export function getProjectSnapshot(projectId) {
  return request(`/projects/${encodeURIComponent(projectId)}/snapshot`)
}
