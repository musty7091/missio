import { apiRequest } from "./httpClient"

export type RegisterPushTokenRequest = {
  fcm_token: string
  device_type?: string | null
  browser_name?: string | null
  platform?: string | null
}

export type PushTokenResponse = {
  id: number
  business_id: number | null
  user_id: number
  device_type: string | null
  browser_name: string | null
  platform: string | null
  is_active: boolean
  last_seen_at_utc: string
}

export type RegisterPushTokenResponse = {
  token: PushTokenResponse
  message: string
}

export type DeactivatePushTokenRequest = {
  fcm_token: string
}

export type DeactivatePushTokenResponse = {
  is_active: boolean
  message: string
}

function getBrowserName() {
  const userAgent = navigator.userAgent.toLowerCase()

  if (userAgent.includes("edg/")) {
    return "Edge"
  }

  if (userAgent.includes("opr/") || userAgent.includes("opera")) {
    return "Opera"
  }

  if (userAgent.includes("chrome")) {
    return "Chrome"
  }

  if (userAgent.includes("firefox")) {
    return "Firefox"
  }

  if (userAgent.includes("safari")) {
    return "Safari"
  }

  return "Bilinmeyen tarayıcı"
}

function getDeviceType() {
  const userAgent = navigator.userAgent.toLowerCase()

  if (userAgent.includes("ipad") || userAgent.includes("tablet")) {
    return "tablet"
  }

  if (
    userAgent.includes("iphone") ||
    userAgent.includes("android") ||
    userAgent.includes("mobile")
  ) {
    return "mobile"
  }

  return "desktop"
}

function getPlatformName() {
  if (navigator.platform && navigator.platform.trim()) {
    return navigator.platform.trim()
  }

  return "unknown"
}

export async function registerCurrentDevicePushToken(fcmToken: string) {
  const payload: RegisterPushTokenRequest = {
    fcm_token: fcmToken,
    device_type: getDeviceType(),
    browser_name: getBrowserName(),
    platform: getPlatformName(),
  }

  return apiRequest<RegisterPushTokenResponse>("/push/tokens", {
    method: "POST",
    body: payload,
    requiresAuth: true,
  })
}



export async function deactivateCurrentDevicePushToken(fcmToken: string) {
  const payload: DeactivatePushTokenRequest = {
    fcm_token: fcmToken,
  }

  return apiRequest<DeactivatePushTokenResponse>("/push/tokens/deactivate", {
    method: "POST",
    body: payload,
    requiresAuth: true,
  })
}
