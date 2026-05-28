import { apiRequest } from "./httpClient"

export type PasswordResetRequestItem = {
  id: number
  business_id: number
  business_name: string | null
  requested_username: string
  target_user_id: number
  target_full_name: string
  target_role: string
  status: string
  requested_at_utc: string
  resolved_at_utc: string | null
  resolved_by_user_id: number | null
}

export type PasswordResetRequestResetResponse = {
  request_id: number
  target_user_id: number
  target_username: string
  temporary_password: string
  must_change_password: boolean
  message: string
}

export function listPasswordResetRequests(statusFilter = "pending") {
  return apiRequest<PasswordResetRequestItem[]>("/password-reset-requests", {
    method: "GET",
    query: {
      status_filter: statusFilter,
    },
  })
}

export function resetPasswordResetRequest(requestId: number) {
  return apiRequest<PasswordResetRequestResetResponse>(
    `/password-reset-requests/${requestId}/reset`,
    {
      method: "POST",
    },
  )
}
