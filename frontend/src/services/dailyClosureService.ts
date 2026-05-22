import { apiRequest } from "./httpClient"

export type DailyOperationClosureItem = {
  id: number
  closure_id: number
  business_id: number
  task_id: number
  task_date: string
  assigned_to_user_id: number | null
  assigned_to_user_full_name: string | null
  assigned_to_username: string | null
  task_title: string
  task_description: string | null
  task_type: string
  task_status: string
  task_priority: string
  requires_photo: boolean
  requires_location: boolean
  requires_manager_approval: boolean
  has_photo_evidence: boolean
  assigned_at_utc: string | null
  started_at_utc: string | null
  completed_at_utc: string | null
  approved_at_utc: string | null
  created_at_utc: string
}

export type DailyOperationClosure = {
  id: number
  business_id: number
  closure_date: string
  closed_by_user_id: number
  closed_by_user_full_name: string
  closed_by_username: string
  closed_by_role: string
  closed_at_utc: string
  status: string
  manager_note: string | null
  total_task_count: number
  completed_task_count: number
  approved_task_count: number
  open_task_count: number
  rejected_task_count: number
  approval_pending_task_count: number
  photo_required_task_count: number
  photo_evidence_task_count: number
  created_at_utc: string
  items: DailyOperationClosureItem[]
}

export type DailyOperationClosureListResponse = {
  closures: DailyOperationClosure[]
  total_count: number
}

export type DailyOperationClosureCreatedResponse = {
  closure: DailyOperationClosure
  message: string
}

export type CreateDailyOperationClosurePayload = {
  closure_date?: string | null
  manager_note?: string | null
}

export function listDailyOperationClosures(params: {
  businessId?: number | null
  limit?: number
  offset?: number
} = {}) {
  return apiRequest<DailyOperationClosureListResponse>("/daily-closures", {
    method: "GET",
    query: {
      business_id: params.businessId,
      limit: params.limit,
      offset: params.offset,
    },
  })
}

export function createDailyOperationClosure(
  payload: CreateDailyOperationClosurePayload,
  params: {
    businessId?: number | null
  } = {},
) {
  return apiRequest<DailyOperationClosureCreatedResponse>("/daily-closures", {
    method: "POST",
    query: {
      business_id: params.businessId,
    },
    body: payload,
  })
}

export function getDailyOperationClosure(closureId: number) {
  return apiRequest<DailyOperationClosure>(`/daily-closures/${closureId}`, {
    method: "GET",
  })
}
