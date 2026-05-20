import { API_BASE_URL } from "../config/api"
import { getAccessToken } from "./authTokenStorage"

type QueryValue = string | number | boolean | null | undefined

type ApiRequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown
  query?: Record<string, QueryValue>
  requiresAuth?: boolean
}

export class ApiError extends Error {
  status: number
  data: unknown

  constructor(message: string, status: number, data: unknown) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.data = data
  }
}

function buildApiUrl(path: string, query?: Record<string, QueryValue>) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`
  const url = new URL(`${API_BASE_URL}${normalizedPath}`)

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== "") {
        url.searchParams.set(key, String(value))
      }
    })
  }

  return url.toString()
}

async function parseResponseBody(response: Response) {
  const contentType = response.headers.get("content-type") || ""

  if (response.status === 204) {
    return null
  }

  if (contentType.includes("application/json")) {
    return response.json()
  }

  return response.text()
}

function getApiErrorMessage(data: unknown, fallback: string) {
  if (typeof data === "object" && data !== null && "detail" in data) {
    const detail = (data as { detail?: unknown }).detail

    if (typeof detail === "string") {
      return detail
    }

    if (Array.isArray(detail)) {
      return "Gönderilen bilgilerde doğrulama hatası var."
    }
  }

  if (typeof data === "object" && data !== null && "message" in data) {
    const message = (data as { message?: unknown }).message

    if (typeof message === "string") {
      return message
    }
  }

  return fallback
}

export async function apiRequest<TResponse>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<TResponse> {
  const { body, query, requiresAuth = true, headers: customHeaders, ...requestOptions } = options
  const headers = new Headers(customHeaders)
  const token = getAccessToken()
  const isFormData = body instanceof FormData

  if (requiresAuth && token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  if (body !== undefined && !isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }

  const response = await fetch(buildApiUrl(path, query), {
    ...requestOptions,
    headers,
    body: body === undefined ? undefined : isFormData ? body : JSON.stringify(body),
  })

  const responseBody = await parseResponseBody(response)

  if (!response.ok) {
    throw new ApiError(
      getApiErrorMessage(responseBody, "Sunucu isteği başarısız oldu."),
      response.status,
      responseBody,
    )
  }

  return responseBody as TResponse
}
