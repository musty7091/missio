export type LocationCheckStatus =
  | "pending"
  | "seen"
  | "shared"
  | "permission_denied"
  | "failed"
  | "expired"
  | "cancelled"

export type LocationCheckNotificationStatus =
  | "not_attempted"
  | "no_subscription"
  | "sent"
  | "partial_failed"
  | "failed"
  | "configuration_error"

export type LocationCheck = {
  id: number
  business_id: number
  request_group_id: string | null
  requested_by_user_id: number | null
  requested_by_user_full_name: string | null
  target_user_id: number
  target_user_full_name: string | null
  target_username: string | null
  status: LocationCheckStatus
  request_note: string | null
  notification_status: LocationCheckNotificationStatus
  notification_attempted_count: number
  notification_sent_count: number
  notification_failed_count: number
  last_notification_attempt_at_utc: string | null
  staff_seen_at_utc: string | null
  responded_at_utc: string | null
  expires_at_utc: string | null
  latitude: number | null
  longitude: number | null
  location_accuracy: number | null
  response_error_code: string | null
  response_error_message: string | null
  requested_at_utc: string
  created_at_utc: string
  updated_at_utc: string
}

export type CreateLocationCheckPayload = {
  target_user_id?: number | null
  target_user_ids?: number[] | null
  request_note?: string | null
}

export type ShareLocationCheckPayload = {
  latitude: number
  longitude: number
  location_accuracy?: number | null
}

export type FailLocationCheckPayload = {
  response_error_code: string
  response_error_message?: string | null
}

export type LocationCheckCreatedResponse = {
  checks: LocationCheck[]
  created_count: number
  message: string
}

export type LocationCheckListResponse = {
  checks: LocationCheck[]
  total_count: number
}

export type LocationCheckUpdatedResponse = {
  check: LocationCheck
  message: string
}
