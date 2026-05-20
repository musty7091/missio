import type { ApiTask, MyTodayTasksResponse } from "../types/apiTask"
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
