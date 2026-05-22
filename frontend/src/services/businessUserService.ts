import { apiRequest } from "./httpClient"

export type BusinessUser = {
  id: number
  business_id: number
  full_name: string
  username: string
  email: string | null
  role: string
  is_active: boolean
  theme_preference: string | null
}

export function listBusinessUsers(businessId: number) {
  return apiRequest<BusinessUser[]>(`/businesses/${businessId}/users`, {
    method: "GET",
  })
}
