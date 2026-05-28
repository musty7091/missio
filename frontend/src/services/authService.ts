import type { LoginRequest, TokenResponse, UserMeResponse } from "../types/auth"
import { apiRequest } from "./httpClient"

export async function loginUser(payload: LoginRequest) {
  return apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    body: payload,
    requiresAuth: false,
  })
}


type ForgotPasswordRequest = {
  business_slug: string
  username: string
}

type ForgotPasswordResponse = {
  message: string
}

export async function requestForgotPassword(payload: ForgotPasswordRequest) {
  return apiRequest<ForgotPasswordResponse>("/auth/forgot-password/request", {
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
