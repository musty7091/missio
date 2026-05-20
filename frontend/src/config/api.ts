export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://127.0.0.1:8000/api/v1"
).replace(/\/+$/, "")

export const ACCESS_TOKEN_STORAGE_KEY = "missio-access-token"
