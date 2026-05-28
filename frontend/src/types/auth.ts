export type LoginRequest = {
  business_slug?: string | null
  username: string
  password: string
}

export type TokenResponse = {
  access_token: string
  token_type: string
  expires_in_minutes: number
}

export type UserMeResponse = {
  id: number
  business_id: number | null
  full_name: string
  username: string
  email: string | null
  role: string
  is_active: boolean
  theme_preference: string | null
  must_change_password: boolean
  subscription_access_status: string
  subscription_status: string | null
  subscription_ends_at_utc: string | null
  subscription_remaining_days: number | null
  subscription_is_expired: boolean
  subscription_lock_reason: string | null
}
