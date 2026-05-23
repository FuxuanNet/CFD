import { request } from './client'

export function setMaterial(payload) {
  return request('/preprocess/material', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function setBoundary(payload) {
  return request('/preprocess/boundary', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function setLoad(payload) {
  return request('/preprocess/load', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
