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
}
