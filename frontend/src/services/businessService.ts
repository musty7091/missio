import type {
  BusinessResponse,
  BusinessSubscriptionOperationResponse,
  BusinessSubscriptionOverviewResponse,
  BusinessSubscriptionPlanChangedResponse,
  BusinessWithOwnerCreatedResponse,
  ChangeBusinessPlanRequest,
  ChangeBusinessSubscriptionPlanRequest,
  CreateBusinessWithOwnerRequest,
  ExtendBusinessSubscriptionRequest,
  SubscriptionPlanResponse,
  UpdateBusinessSubscriptionStatusRequest,
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

export async function listSubscriptionPlans() {
  return apiRequest<SubscriptionPlanResponse[]>("/businesses/subscription-plans", {
    method: "GET",
    requiresAuth: true,
  })
}

export async function getBusinessSubscriptionOverview(businessId: number) {
  return apiRequest<BusinessSubscriptionOverviewResponse>(
    `/businesses/${businessId}/subscription/overview`,
    {
      method: "GET",
      requiresAuth: true,
    },
  )
}

export async function extendBusinessSubscription(
  businessId: number,
  payload: ExtendBusinessSubscriptionRequest,
) {
  return apiRequest<BusinessSubscriptionOperationResponse>(
    `/businesses/${businessId}/subscription/extend`,
    {
      method: "POST",
      body: payload,
      requiresAuth: true,
    },
  )
}

export async function changeBusinessPlan(
  businessId: number,
  payload: ChangeBusinessPlanRequest,
) {
  return apiRequest<BusinessSubscriptionOperationResponse>(
    `/businesses/${businessId}/subscription/change-plan`,
    {
      method: "POST",
      body: payload,
      requiresAuth: true,
    },
  )
}

export async function updateBusinessSubscriptionStatus(
  businessId: number,
  payload: UpdateBusinessSubscriptionStatusRequest,
) {
  return apiRequest<BusinessSubscriptionOperationResponse>(
    `/businesses/${businessId}/subscription/status`,
    {
      method: "POST",
      body: payload,
      requiresAuth: true,
    },
  )
}

/**
 * Geçici uyumluluk fonksiyonu.
 * Eski SuperAdminPlanPanel tamamen yeniden yazılana kadar build bozulmasın diye tutuluyor.
 * Yeni ekranda changeBusinessPlan kullanılacak.
 */
export async function changeBusinessSubscriptionPlan(
  businessId: number,
  payload: ChangeBusinessSubscriptionPlanRequest,
) {
  return apiRequest<BusinessSubscriptionPlanChangedResponse>(
    `/businesses/${businessId}/subscription/change-plan`,
    {
      method: "POST",
      body: payload,
      requiresAuth: true,
    },
  )
}
