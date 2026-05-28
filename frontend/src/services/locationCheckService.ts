import { apiRequest } from "./httpClient"
import type {
  CreateLocationCheckPayload,
  FailLocationCheckPayload,
  LocationCheckCreatedResponse,
  LocationCheckListResponse,
  LocationCheckUpdatedResponse,
  ShareLocationCheckPayload,
} from "../types/locationCheck"

export type ListLocationChecksParams = {
  businessId?: number
  status?: string | null
  targetUserId?: number | null
  limit?: number
  offset?: number
}

export function createLocationCheck(
  payload: CreateLocationCheckPayload,
  businessId?: number,
) {
  return apiRequest<LocationCheckCreatedResponse>("/location-checks", {
    method: "POST",
    query: {
      business_id: businessId,
    },
    body: payload,
  })
}

export function listLocationChecks(params: ListLocationChecksParams = {}) {
  return apiRequest<LocationCheckListResponse>("/location-checks", {
    method: "GET",
    query: {
      business_id: params.businessId,
      status: params.status,
      target_user_id: params.targetUserId,
      limit: params.limit,
      offset: params.offset,
    },
  })
}

export function listMyPendingLocationChecks() {
  return apiRequest<LocationCheckListResponse>("/location-checks/my-pending", {
    method: "GET",
  })
}

export function markLocationCheckSeen(locationCheckId: number) {
  return apiRequest<LocationCheckUpdatedResponse>(
    `/location-checks/${locationCheckId}/seen`,
    {
      method: "POST",
    },
  )
}

export function shareLocationCheck(
  locationCheckId: number,
  payload: ShareLocationCheckPayload,
) {
  return apiRequest<LocationCheckUpdatedResponse>(
    `/location-checks/${locationCheckId}/share`,
    {
      method: "POST",
      body: payload,
    },
  )
}

export function failLocationCheck(
  locationCheckId: number,
  payload: FailLocationCheckPayload,
) {
  return apiRequest<LocationCheckUpdatedResponse>(
    `/location-checks/${locationCheckId}/fail`,
    {
      method: "POST",
      body: payload,
    },
  )
}
