import type {
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
