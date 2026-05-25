import type { UserMeResponse } from "../types/auth"
import { apiRequest } from "./httpClient"

export type ChangeOwnPasswordRequest = {
  current_password: string
  new_password: string
  new_password_repeat: string
}

export type ChangeOwnPasswordResponse = {
  message: string
}

export type UpdateMyProfileRequest = {
  full_name: string
  email: string | null
}

export type UpdateMyProfileResponse = {
  user: UserMeResponse
  message: string
}

export async function changeOwnPassword(payload: ChangeOwnPasswordRequest) {
  return apiRequest<ChangeOwnPasswordResponse>("/auth/me/password", {
    method: "POST",
    body: payload,
    requiresAuth: true,
  })
}

export async function updateMyProfile(payload: UpdateMyProfileRequest) {
  return apiRequest<UpdateMyProfileResponse>("/auth/me/profile", {
    method: "PATCH",
    body: payload,
    requiresAuth: true,
  })
}
