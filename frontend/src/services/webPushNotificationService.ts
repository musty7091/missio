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
  expirationTime: number | null
  keys: WebPushSubscriptionKeysRequest
  contentEncoding: string
  device_type?: string | null
  browser_name?: string | null
  platform?: string | null
}

type WebPushSubscriptionResponse = {
  id: number
  business_id: number | null
  user_id: number
  device_type: string | null
  browser_name: string | null
  platform: string | null
  is_active: boolean
  last_seen_at_utc: string
}

type RegisterWebPushSubscriptionResponse = {
  subscription: WebPushSubscriptionResponse
  message: string
}

type DeactivateWebPushSubscriptionResponse = {
  is_active: boolean
  message: string
}

type SendWebPushTestResponse = {
  attempted_count: number
  sent_count: number
  failed_count: number
  message: string
}

export type MissioWebPushEnableResult = {
  ok: boolean
  message: string
  subscription?: PushSubscription
}

const WEB_PUSH_SERVICE_WORKER_PATH = "/sw.js"
const WEB_PUSH_DISABLED_STORAGE_KEY = "missio-web-push-notifications-disabled"
const WEB_PUSH_ENDPOINT_STORAGE_KEY = "missio-web-push-endpoint"

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
  const base64 = `${base64String}${padding}`
    .replace(/-/g, "+")
    .replace(/_/g, "/")

  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)

  for (let index = 0; index < rawData.length; index += 1) {
    outputArray[index] = rawData.charCodeAt(index)
  }

  return outputArray
}

function getSupportedContentEncoding() {
  const pushManagerWithEncodings = PushManager as typeof PushManager & {
    supportedContentEncodings?: string[]
  }

  if (
    Array.isArray(pushManagerWithEncodings.supportedContentEncodings) &&
    pushManagerWithEncodings.supportedContentEncodings.includes("aes128gcm")
  ) {
    return "aes128gcm"
  }

  return "aes128gcm"
}

function getSubscriptionKeys(subscription: PushSubscription) {
  const subscriptionJson = subscription.toJSON()

  const p256dh = subscriptionJson.keys?.p256dh
  const auth = subscriptionJson.keys?.auth

  if (!p256dh || !auth) {
    throw new Error("Tarayıcı Web Push anahtarları alınamadı.")
  }

  return {
    p256dh,
    auth,
  }
}

function rememberWebPushEndpoint(subscription: PushSubscription) {
  localStorage.setItem(WEB_PUSH_ENDPOINT_STORAGE_KEY, subscription.endpoint)
}

function rememberWebPushEnabledState(enabled: boolean) {
  localStorage.setItem(
    WEB_PUSH_DISABLED_STORAGE_KEY,
    enabled ? "false" : "true",
  )
}

export function getWebPushPermissionStatus() {
  if (!("Notification" in window)) {
    return "unsupported"
  }

  return Notification.permission
}

export function isWebPushLocallyEnabled() {
  return (
    getWebPushPermissionStatus() === "granted" &&
    localStorage.getItem(WEB_PUSH_DISABLED_STORAGE_KEY) !== "true"
  )
}

export async function getWebPushPublicKey() {
  return apiRequest<WebPushPublicKeyResponse>("/push/web/public-key", {
    method: "GET",
    requiresAuth: true,
  })
}

async function getReadyWebPushRegistration() {
  if (!("serviceWorker" in navigator)) {
    throw new Error("Bu tarayıcı service worker desteklemiyor.")
  }

  if (!("PushManager" in window)) {
    throw new Error("Bu tarayıcı Web Push desteklemiyor.")
  }

  const registration = await navigator.serviceWorker.register(
    WEB_PUSH_SERVICE_WORKER_PATH,
  )

  return registration
}

async function getExistingOrNewSubscription(
  registration: ServiceWorkerRegistration,
  vapidPublicKey: string,
) {
  const existingSubscription = await registration.pushManager.getSubscription()

  if (existingSubscription) {
    return existingSubscription
  }

  return registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
  })
}

export async function requestMissioWebPushPermissionAndSubscribe(): Promise<MissioWebPushEnableResult> {
  if (!window.isSecureContext) {
    return {
      ok: false,
      message: "Web Push için HTTPS bağlantı gerekli. Cloudflare linki üzerinden deneyin.",
    }
  }

  if (!("Notification" in window)) {
    return {
      ok: false,
      message: "Bu tarayıcı bildirim desteklemiyor.",
    }
  }

  if (Notification.permission === "denied") {
    return {
      ok: false,
      message: "Tarayıcı bildirim izni engellenmiş. Site ayarlarından izni açmanız gerekiyor.",
    }
  }

  const publicKeyResponse = await getWebPushPublicKey()

  if (!publicKeyResponse.enabled || !publicKeyResponse.public_key) {
    return {
      ok: false,
      message: "Web Push sistemi backend tarafında aktif değil.",
    }
  }

  const permission = await Notification.requestPermission()

  if (permission !== "granted") {
    return {
      ok: false,
      message: "Bildirim izni verilmedi.",
    }
  }

  const registration = await getReadyWebPushRegistration()
  const subscription = await getExistingOrNewSubscription(
    registration,
    publicKeyResponse.public_key,
  )
  const keys = getSubscriptionKeys(subscription)

  const payload: RegisterWebPushSubscriptionRequest = {
    endpoint: subscription.endpoint,
    expirationTime: subscription.expirationTime,
    keys,
    contentEncoding: getSupportedContentEncoding(),
    device_type: getDeviceType(),
    browser_name: getBrowserName(),
    platform: getPlatformName(),
  }

  await apiRequest<RegisterWebPushSubscriptionResponse>(
    "/push/web/subscriptions",
    {
      method: "POST",
      body: payload,
      requiresAuth: true,
    },
  )

  rememberWebPushEndpoint(subscription)
  rememberWebPushEnabledState(true)

  return {
    ok: true,
    message: "Bu cihaz için Web Push bildirimleri açık.",
    subscription,
  }
}

export async function deactivateCurrentWebPushSubscription() {
  const registration = await getReadyWebPushRegistration()
  const subscription = await registration.pushManager.getSubscription()
  const storedEndpoint = localStorage.getItem(WEB_PUSH_ENDPOINT_STORAGE_KEY)

  const endpoint = subscription?.endpoint ?? storedEndpoint

  if (endpoint) {
    await apiRequest<DeactivateWebPushSubscriptionResponse>(
      "/push/web/subscriptions/deactivate",
      {
        method: "POST",
        body: {
          endpoint,
        },
        requiresAuth: true,
      },
    )
  }

  if (subscription) {
    await subscription.unsubscribe()
  }

  rememberWebPushEnabledState(false)
  localStorage.removeItem(WEB_PUSH_ENDPOINT_STORAGE_KEY)

  return {
    is_active: false,
    message: "Bu cihaz için Web Push bildirimleri kapatıldı.",
  }
}

export async function sendCurrentUserWebPushTest() {
  return apiRequest<SendWebPushTestResponse>("/push/web/test", {
    method: "POST",
    body: {
      title: "Missio Web Push test",
      body: "Firebase kullanmadan standart Web Push bildirimi çalışıyor.",
    },
    requiresAuth: true,
  })
}
