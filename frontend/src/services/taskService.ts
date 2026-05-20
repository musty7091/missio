import type { MyTodayTasksResponse } from "../types/apiTask"
import { apiRequest } from "./httpClient"

type GetMyTodayTasksParams = {
  businessId?: number
  taskDate?: string
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
