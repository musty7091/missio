import { apiRequest } from "./httpClient"

export type BusinessUserRole = "boss" | "manager" | "staff"

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

export type BusinessUserMutationResponse = {
  user: BusinessUser
  message: string
}

export type CreateBusinessUserPayload = {
  full_name: string
  username: string
  password: string
  role: BusinessUserRole
  email?: string | null
  theme_preference?: string | null
}

export type UpdateBusinessUserPayload = {
  full_name?: string
  email?: string | null
  theme_preference?: string | null
  is_active?: boolean
}

export type ResetBusinessUserPasswordPayload = {
  new_password: string
}

export type ChangeBusinessUserRolePayload = {
  role: "manager" | "staff"
}

export function listBusinessUsers(businessId: number) {
  return apiRequest<BusinessUser[]>(`/businesses/${businessId}/users`, {
    method: "GET",
  })
}

export function createBusinessUser(
  businessId: number,
  payload: CreateBusinessUserPayload,
) {
  return apiRequest<BusinessUserMutationResponse>(`/businesses/${businessId}/users`, {
    method: "POST",
    body: payload,
  })
}

export function updateBusinessUser(
  businessId: number,
  userId: number,
  payload: UpdateBusinessUserPayload,
) {
  return apiRequest<BusinessUserMutationResponse>(
    `/businesses/${businessId}/users/${userId}`,
    {
      method: "PATCH",
      body: payload,
    },
  )
}

export function setBusinessUserActiveStatus(
  businessId: number,
  userId: number,
  isActive: boolean,
) {
  return updateBusinessUser(businessId, userId, {
    is_active: isActive,
  })
}

export function resetBusinessUserPassword(
  businessId: number,
  userId: number,
  payload: ResetBusinessUserPasswordPayload,
) {
  return apiRequest<BusinessUserMutationResponse>(
    `/businesses/${businessId}/users/${userId}/reset-password`,
    {
      method: "POST",
      body: payload,
    },
  )
}

export function changeBusinessUserRole(
  businessId: number,
  userId: number,
  payload: ChangeBusinessUserRolePayload,
) {
  return apiRequest<BusinessUserMutationResponse>(
    `/businesses/${businessId}/users/${userId}/change-role`,
    {
      method: "POST",
      body: payload,
    },
  )
}