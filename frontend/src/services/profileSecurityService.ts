import { apiRequest } from "./httpClient"

export type ChangeOwnPasswordRequest = {
  current_password: string
  new_password: string
  new_password_repeat: string
}

export type ChangeOwnPasswordResponse = {
  message: string
}

export async function changeOwnPassword(payload: ChangeOwnPasswordRequest) {
  return apiRequest<ChangeOwnPasswordResponse>("/auth/me/password", {
    method: "POST",
    body: payload,
    requiresAuth: true,
  })
}
