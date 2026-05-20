import type { LoginRequest, TokenResponse, UserMeResponse } from "../types/auth"
import { apiRequest } from "./httpClient"

export async function loginUser(payload: LoginRequest) {
  return apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    body: payload,
    requiresAuth: false,
  })
}

export async function getCurrentUser() {
  return apiRequest<UserMeResponse>("/auth/me", {
    method: "GET",
    requiresAuth: true,
  })
}
