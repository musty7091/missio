export type CreateBusinessWithOwnerRequest = {
  business_name: string
  business_slug: string

  owner_full_name: string
  owner_username: string
  owner_password: string

  business_owner_name?: string | null
  business_phone?: string | null
  business_email?: string | null
  business_address?: string | null

  owner_email?: string | null
  owner_role?: "boss"

  timezone?: string
  default_theme?: string
}

export type BusinessResponse = {
  id: number
  name: string
  slug: string
  logo_path: string | null
  owner_name: string | null
  phone: string | null
  email: string | null
  address: string | null
  timezone: string
  default_theme: string
  is_active: boolean
  created_at: string
  updated_at: string

  subscription_status: string | null
  subscription_billing_period: string | null
  subscription_plan_code: string | null
  subscription_plan_name: string | null
  subscription_ends_at_utc: string | null
  subscription_max_users: number | null
  subscription_remaining_days: number | null
}

export type BusinessOwnerUserResponse = {
  id: number
  business_id: number
  full_name: string
  username: string
  email: string | null
  role: string
  is_active: boolean
}

export type BusinessSubscriptionResponse = {
  id: number
  business_id: number
  plan_id: number
  status: string
  billing_period: string
  starts_at_utc: string
  ends_at_utc: string | null
  is_current: boolean
  max_users_snapshot: number
  max_managers_snapshot: number | null
  max_daily_tasks_snapshot: number | null
  report_retention_days_snapshot: number
}

export type BusinessWithOwnerCreatedResponse = {
  business: BusinessResponse
  owner_user: BusinessOwnerUserResponse
  subscription: BusinessSubscriptionResponse | null
  message: string
}

export type SubscriptionPlanResponse = {
  id: number
  code: string
  name: string
  description: string | null
  max_users: number
  max_managers: number | null
  max_daily_tasks: number | null
  report_retention_days: number
  price_monthly: string | null
  price_yearly: string | null
  currency: string
  display_order: number
  is_active: boolean
}

export type BusinessSubscriptionOverviewResponse = {
  business: BusinessResponse
  current_subscription: BusinessSubscriptionResponse | null
  current_plan: SubscriptionPlanResponse | null
  active_user_count: number
  remaining_days: number | null
  is_expired: boolean
  available_plans: SubscriptionPlanResponse[]
}

export type ExtendBusinessSubscriptionRequest = {
  duration_days: number
  billing_period: "manual" | "trial" | "monthly" | "yearly" | "custom"
  notes?: string | null
}

export type ChangeBusinessPlanRequest = {
  plan_code: string
  preserve_remaining_time: boolean
  notes?: string | null
}

export type UpdateBusinessSubscriptionStatusRequest = {
  status: "active" | "suspended" | "cancelled"
  notes?: string | null
}

export type BusinessSubscriptionOperationResponse = {
  subscription: BusinessSubscriptionResponse
  message: string
}

/**
 * Geçici uyumluluk tipi.
 * Eski plan paneli tamamen kaldırılana kadar build bozulmasın diye tutuluyor.
 * Yeni ekranda ChangeBusinessPlanRequest kullanılacak.
 */
export type ChangeBusinessSubscriptionPlanRequest = {
  plan_code: string
  duration_days?: number
  billing_period?: "manual" | "trial" | "monthly" | "yearly" | "custom"
  status?: "trialing" | "active" | "suspended" | "cancelled" | "expired"
  change_mode?: "replace" | "extend"
  notes?: string | null
}

export type BusinessSubscriptionPlanChangedResponse =
  BusinessSubscriptionOperationResponse
