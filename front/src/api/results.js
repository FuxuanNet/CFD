import { request } from './client'

export function getResultSummary(resultId) {
  return request(`/results/${encodeURIComponent(resultId)}/summary`)
}

export function getResultField(resultId, field) {
  return request(`/results/${encodeURIComponent(resultId)}/field?field=${encodeURIComponent(field)}`)
}
