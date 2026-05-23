import { request } from './client'

export function listSolverPlugins() {
  return request('/solver/plugins')
}

export function runStaticSolve(payload) {
  return request('/solver/run', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function startSolverTask(payload) {
  return request('/solver/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
