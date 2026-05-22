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

export type TaskEvent = {
  id: number
  business_id: number
  task_id: number
  user_id: number | null
  event_type: string
  old_status: string | null
  new_status: string | null
  note: string | null
  latitude: number | null
  longitude: number | null
  location_accuracy: number | null
  ip_address: string | null
  user_agent: string | null
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

type DeleteTaskAttachmentResponse = {
  attachment_id: number
  message: string
}

type TaskEventListResponse = {
  events: TaskEvent[]
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

export function deleteTaskAttachment(taskId: number, attachmentId: number) {
  return apiRequest<DeleteTaskAttachmentResponse>(
    `/tasks/${taskId}/attachments/${attachmentId}`,
    {
      method: "DELETE",
    },
  )
}

export function listTaskEvents(taskId: number) {
  return apiRequest<TaskEventListResponse>(`/tasks/${taskId}/events`, {
    method: "GET",
  })
}

export function getTaskAttachmentFileBlob(taskId: number, attachmentId: number) {
  return apiFileRequest(`/tasks/${taskId}/attachments/${attachmentId}/file`)
}

export type BusinessTaskListResponse = {
  tasks: ApiTask[]
  total_count: number
}

type ListBusinessTasksParams = {
  businessId?: number
  taskDate?: string
  taskType?: string
  status?: string
  assignedToUserId?: number
  limit?: number
  offset?: number
}

export function listBusinessTasks(params: ListBusinessTasksParams = {}) {
  return apiRequest<BusinessTaskListResponse>("/tasks", {
    method: "GET",
    query: {
      business_id: params.businessId,
      task_date: params.taskDate,
      task_type: params.taskType,
      status: params.status,
      assigned_to_user_id: params.assignedToUserId,
      limit: params.limit,
      offset: params.offset,
    },
  })
}

export function approveTask(taskId: number, payload: ChangeTaskPayload = {}) {
  return apiRequest<TaskStatusChangedResponse>(`/tasks/${taskId}/approve`, {
    method: "POST",
    body: payload,
  })
}

export function rejectTask(taskId: number, payload: { note: string }) {
  return apiRequest<TaskStatusChangedResponse>(`/tasks/${taskId}/reject`, {
    method: "POST",
    body: payload,
  })
}


export type CreateExtraTaskPayload = {
  assigned_to_user_id: number
  title: string
  description?: string | null
  category_id?: number | null
  priority: "low" | "normal" | "high" | "urgent"
  due_at_utc?: string | null
  requires_photo: boolean
  requires_location: boolean
  requires_manager_approval: boolean
}

type TaskCreatedResponse = {
  task: ApiTask
  message: string
}

export function createExtraTask(payload: CreateExtraTaskPayload) {
  return apiRequest<TaskCreatedResponse>("/tasks/extra", {
    method: "POST",
    body: payload,
  })
}


export type CreateRoutineTaskTemplatePayload = {
  assigned_to_user_id: number
  title: string
  description?: string | null
  category_id?: number | null
  recurrence_type: "daily"
  default_priority: "low" | "normal" | "high" | "urgent"
  default_due_time_local?: string | null
  default_due_offset_minutes?: number | null
  requires_photo: boolean
  requires_location: boolean
  requires_manager_approval: boolean
}

export type TaskTemplateResponse = {
  id: number
  business_id: number
  assigned_to_user_id: number
  created_by_user_id: number | null
  title: string
  description: string | null
  category_id: number | null
  recurrence_type: string
  default_priority: string
  default_due_time_local: string | null
  default_due_offset_minutes: number | null
  requires_photo: boolean
  requires_location: boolean
  requires_manager_approval: boolean
  is_active: boolean
  created_at_utc: string
  updated_at_utc: string
}

type TaskTemplateCreatedResponse = {
  template: TaskTemplateResponse
  message: string
}

export function createRoutineTaskTemplate(payload: CreateRoutineTaskTemplatePayload) {
  return apiRequest<TaskTemplateCreatedResponse>("/tasks/routine-templates", {
    method: "POST",
    body: payload,
  })
}

export type GenerateDailyRoutineTasksPayload = {
  task_date?: string | null
  assigned_to_user_id?: number | null
}

type DailyRoutineTasksGeneratedResponse = {
  task_date: string
  created_count: number
  skipped_count: number
  tasks: ApiTask[]
  message: string
}

export function generateDailyRoutineTasks(payload: GenerateDailyRoutineTasksPayload) {
  return apiRequest<DailyRoutineTasksGeneratedResponse>("/tasks/generate-daily-routines", {
    method: "POST",
    body: payload,
  })
}
