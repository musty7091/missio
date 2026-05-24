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
