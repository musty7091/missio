import { API_BASE_URL } from "../config/api"
import { getAccessToken } from "./authTokenStorage"
import { apiRequest } from "./httpClient"

export type DailyOperationClosureItem = {
  id: number
  closure_id: number
  business_id: number
  task_id: number
  task_date: string
  assigned_to_user_id: number | null
  assigned_to_user_full_name: string | null
  assigned_to_username: string | null
  task_title: string
  task_description: string | null
  task_type: string
  task_status: string
  task_priority: string
  requires_photo: boolean
  requires_location: boolean
  requires_manager_approval: boolean
  has_photo_evidence: boolean
  assigned_at_utc: string | null
  started_at_utc: string | null
  completed_at_utc: string | null
  approved_at_utc: string | null
  created_at_utc: string
}

export type DailyOperationClosure = {
  id: number
  business_id: number
  closure_date: string
  closed_by_user_id: number | null
  closed_by_user_full_name: string
  closed_by_username: string
  closed_by_role: string
  closed_at_utc: string
  status: string
  manager_note: string | null
  closed_by_system: boolean
  total_task_count: number
  completed_task_count: number
  approved_task_count: number
  open_task_count: number
  rejected_task_count: number
  approval_pending_task_count: number
  photo_required_task_count: number
  photo_evidence_task_count: number
  created_at_utc: string
  items: DailyOperationClosureItem[]
}

export type DailyOperationClosureListResponse = {
  closures: DailyOperationClosure[]
  total_count: number
}

export type DailyOperationClosureCreatedResponse = {
  closure: DailyOperationClosure
  message: string
}

export type CreateDailyOperationClosurePayload = {
  closure_date?: string | null
  manager_note?: string | null
}

export type DownloadedDailyClosurePdf = {
  blob: Blob
  filename: string
}

function resolveApiBaseUrl() {
  if (API_BASE_URL.startsWith("/")) {
    return `${window.location.origin}${API_BASE_URL}`
  }

  return API_BASE_URL.replace(/\/+$/, "")
}

function buildPdfUrl(closureId: number) {
  return `${resolveApiBaseUrl()}/daily-closures/${closureId}/pdf`
}

function getFilenameFromContentDisposition(value: string | null) {
  if (!value) {
    return null
  }

  const match = value.match(/filename="?([^"]+)"?/i)

  if (!match || !match[1]) {
    return null
  }

  return match[1]
}

async function getDownloadErrorMessage(response: Response) {
  const contentType = response.headers.get("content-type") || ""

  if (contentType.includes("application/json")) {
    const data = await response.json().catch(() => null)

    if (data && typeof data === "object" && "detail" in data) {
      const detail = (data as { detail?: unknown }).detail

      if (typeof detail === "string") {
        return detail
      }
    }
  }

  const text = await response.text().catch(() => "")

  return text || "PDF indirilemedi."
}

export function listDailyOperationClosures(params: {
  businessId?: number | null
  limit?: number
  offset?: number
} = {}) {
  return apiRequest<DailyOperationClosureListResponse>("/daily-closures", {
    method: "GET",
    query: {
      business_id: params.businessId,
      limit: params.limit,
      offset: params.offset,
    },
  })
}

export function createDailyOperationClosure(
  payload: CreateDailyOperationClosurePayload,
  params: {
    businessId?: number | null
  } = {},
) {
  return apiRequest<DailyOperationClosureCreatedResponse>("/daily-closures", {
    method: "POST",
    query: {
      business_id: params.businessId,
    },
    body: payload,
  })
}

export function getDailyOperationClosure(closureId: number) {
  return apiRequest<DailyOperationClosure>(`/daily-closures/${closureId}`, {
    method: "GET",
  })
}

export async function downloadDailyOperationClosurePdf(
  closureId: number,
): Promise<DownloadedDailyClosurePdf> {
  const token = getAccessToken()
  const headers = new Headers()

  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  const response = await fetch(buildPdfUrl(closureId), {
    method: "GET",
    headers,
  })

  if (!response.ok) {
    throw new Error(await getDownloadErrorMessage(response))
  }

  const blob = await response.blob()
  const filename =
    getFilenameFromContentDisposition(response.headers.get("content-disposition")) ||
    `missio-gun-sonu-raporu-${closureId}.pdf`

  return {
    blob,
    filename,
  }
}
