import type { ApiTask, MyTodayTasksResponse } from "../types/apiTask"
import { API_BASE_URL } from "../config/api"
import { getAccessToken } from "./authTokenStorage"
import { apiRequest } from "./httpClient"

type GetMyTodayTasksParams = {
  businessId?: number
  taskDate?: string
}

type TaskStatusChangedResponse = {
  task: ApiTask
  message: string
}

type ChangeTaskPayload = {
  note?: string | null
  latitude?: number | null
  longitude?: number | null
  location_accuracy?: number | null
}

export type TaskAttachment = {
  id: number
  business_id: number
  task_id: number
  event_id: number | null
  uploaded_by_user_id: number | null
  file_name: string
  file_type: string | null
  file_size: number | null
  latitude: number | null
  longitude: number | null
  location_accuracy: number | null
  created_at_utc: string
}

type UploadTaskAttachmentResponse = {
  attachment: TaskAttachment
  message: string
}

type TaskAttachmentListResponse = {
  attachments: TaskAttachment[]
  total_count: number
}

type UploadTaskAttachmentPayload = {
  file: File
  latitude?: number | null
  longitude?: number | null
  location_accuracy?: number | null
}

function resolveApiBaseUrl() {
  if (API_BASE_URL.startsWith("/")) {
    return `${window.location.origin}${API_BASE_URL}`
  }

  return API_BASE_URL.replace(/\/+$/, "")
}

function buildApiUrl(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`
  return `${resolveApiBaseUrl()}${normalizedPath}`
}

async function apiFileRequest(path: string) {
  const token = getAccessToken()
  const headers = new Headers()

  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  const response = await fetch(buildApiUrl(path), {
    method: "GET",
    headers,
  })

  if (!response.ok) {
    throw new Error("Fotoğraf dosyası alınamadı.")
  }

  return response.blob()
}

export function getMyTodayTasks(params: GetMyTodayTasksParams = {}) {
  return apiRequest<MyTodayTasksResponse>("/tasks/my-today", {
    method: "GET",
    query: {
      business_id: params.businessId,
      task_date: params.taskDate,
    },
  })
}

export function startTask(taskId: number, payload: ChangeTaskPayload = {}) {
  return apiRequest<TaskStatusChangedResponse>(`/tasks/${taskId}/start`, {
    method: "POST",
    body: payload,
  })
}

export function completeTask(taskId: number, payload: ChangeTaskPayload = {}) {
  return apiRequest<TaskStatusChangedResponse>(`/tasks/${taskId}/complete`, {
    method: "POST",
    body: payload,
  })
}

export function uploadTaskAttachment(taskId: number, payload: UploadTaskAttachmentPayload) {
  const formData = new FormData()

  formData.append("file", payload.file)

  if (payload.latitude !== undefined && payload.latitude !== null) {
    formData.append("latitude", String(payload.latitude))
  }

  if (payload.longitude !== undefined && payload.longitude !== null) {
    formData.append("longitude", String(payload.longitude))
  }

  if (payload.location_accuracy !== undefined && payload.location_accuracy !== null) {
    formData.append("location_accuracy", String(payload.location_accuracy))
  }

  return apiRequest<UploadTaskAttachmentResponse>(`/tasks/${taskId}/attachments`, {
    method: "POST",
    body: formData,
  })
}

export function listTaskAttachments(taskId: number) {
  return apiRequest<TaskAttachmentListResponse>(`/tasks/${taskId}/attachments`, {
    method: "GET",
  })
}

export function getTaskAttachmentFileBlob(taskId: number, attachmentId: number) {
  return apiFileRequest(`/tasks/${taskId}/attachments/${attachmentId}/file`)
}
