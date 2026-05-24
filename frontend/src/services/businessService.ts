import type {
  BusinessResponse,
  BusinessWithOwnerCreatedResponse,
  CreateBusinessWithOwnerRequest,
} from "../types/business"
import { apiRequest } from "./httpClient"

export async function createBusinessWithOwner(payload: CreateBusinessWithOwnerRequest) {
  return apiRequest<BusinessWithOwnerCreatedResponse>("/businesses", {
    method: "POST",
    body: payload,
    requiresAuth: true,
  })
}

export async function listBusinesses() {
  return apiRequest<BusinessResponse[]>("/businesses", {
    method: "GET",
    requiresAuth: true,
  })
}
