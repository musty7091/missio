import { apiRequest } from "./httpClient"

type WebPushPublicKeyResponse = {
  enabled: boolean
  public_key: string
  subject: string
}

type WebPushSubscriptionKeysRequest = {
  p256dh: string
  auth: string
}

type RegisterWebPushSubscriptionRequest = {
  endpoint: string
  expirationTime?: number | null
  keys: WebPushSubscriptionKeysRequest
  contentEncoding?: string | null
  device_type?: string | null
  browser_name?: string | null
  platform?: string | null
}

type WebPushRegistrationResult = {
  status:
    | "registered"
    | "unsupported"
    | "disabled"
    | "permission_denied"
    | "missing_subscription_data"
  message: string
}

let inFlightRegistration: Promise<WebPushRegistrationResult> | null = null

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

function urlBase64ToUint8Array(base64String: string) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4)
  const base64 = `${base64String}${padding}`.replace(/-/g, "+").replace(/_/g, "/")
  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)

  for (let index = 0; index < rawData.length; index += 1) {
    outputArray[index] = rawData.charCodeAt(index)
  }

  return outputArray
}

function isWebPushSupported() {
  return (
    "serviceWorker" in navigator &&
    "PushManager" in window &&
    "Notification" in window
  )
}

async function getWebPushPublicKey() {
  return apiRequest<WebPushPublicKeyResponse>("/push/web/public-key", {
    method: "GET",
    requiresAuth: true,
  })
}

async function resolveNotificationPermission() {
  if (Notification.permission === "granted") {
    return "granted"
  }

  if (Notification.permission === "denied") {
    return "denied"
  }

  return Notification.requestPermission()
}

async function registerCurrentDeviceWebPushSubscriptionInternal(): Promise<WebPushRegistrationResult> {
  if (!isWebPushSupported()) {
    return {
      status: "unsupported",
      message: "Bu cihaz Web Push bildirimlerini desteklemiyor.",
    }
  }

  const publicKeyResponse = await getWebPushPublicKey()

  if (!publicKeyResponse.enabled || !publicKeyResponse.public_key) {
    return {
      status: "disabled",
      message: "Web Push sistemi aktif değil.",
    }
  }

  const permission = await resolveNotificationPermission()

  if (permission !== "granted") {
    return {
      status: "permission_denied",
      message: "Bildirim izni verilmedi.",
    }
  }

  const registration = await navigator.serviceWorker.ready

  let subscription = await registration.pushManager.getSubscription()

  if (!subscription) {
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicKeyResponse.public_key),
    })
  }

  const subscriptionJson = subscription.toJSON()
  const endpoint = subscription.endpoint
  const p256dh = subscriptionJson.keys?.p256dh
  const auth = subscriptionJson.keys?.auth

  if (!endpoint || !p256dh || !auth) {
    return {
      status: "missing_subscription_data",
      message: "Bildirim aboneliği eksik üretildi.",
    }
  }

  const payload: RegisterWebPushSubscriptionRequest = {
    endpoint,
    expirationTime: subscriptionJson.expirationTime ?? null,
    keys: {
      p256dh,
      auth,
    },
    contentEncoding: "aes128gcm",
    device_type: getDeviceType(),
    browser_name: getBrowserName(),
    platform: getPlatformName(),
  }

  await apiRequest("/push/web/subscriptions", {
    method: "POST",
    body: payload,
    requiresAuth: true,
  })

  return {
    status: "registered",
    message: "Web Push cihazı kaydedildi.",
  }
}

export async function registerCurrentDeviceWebPushSubscription() {
  if (!inFlightRegistration) {
    inFlightRegistration = registerCurrentDeviceWebPushSubscriptionInternal()
      .finally(() => {
        inFlightRegistration = null
      })
  }

  return inFlightRegistration
}