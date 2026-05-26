const DEFAULT_API_BASE_URL = "/api/v1"

function normalizeApiBaseUrl(value: string | undefined) {
  const apiBaseUrl = value?.trim() || DEFAULT_API_BASE_URL

  return apiBaseUrl.replace(/\/+$/, "")
}

export const API_BASE_URL = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL)

export const ACCESS_TOKEN_STORAGE_KEY = "missio-access-token"
