import { ACCESS_TOKEN_STORAGE_KEY } from "../config/api"

export function getAccessToken() {
  return window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)
}

export function setAccessToken(token: string) {
  window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token)
}

export function clearAccessToken() {
  window.localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY)
}
