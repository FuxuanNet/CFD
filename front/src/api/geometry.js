import { request } from './client'

export function createBoxGeometry(payload) {
  return request('/geometry/box', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function createSphereGeometry(payload) {
  return request('/geometry/sphere', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function createCylinderGeometry(payload) {
  return request('/geometry/cylinder', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function importStepGeometry(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request('/geometry/step', {
    method: 'POST',
    body: formData,
  })
}
