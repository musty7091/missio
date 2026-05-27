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

const WEB_PUSH_ENDPOINT_STORAGE_KEY = "missio-web-push-endpoint"
const WEB_PUSH_DISABLED_STORAGE_KEY = "missio-web-push-notifications-disabled"

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

async function unregisterLegacyFirebaseMessagingServiceWorkers() {
  if (!("serviceWorker" in navigator)) {
    return
  }

  const registrations = await navigator.serviceWorker.getRegistrations()

  await Promise.all(
    registrations.map(async (registration) => {
      const scriptUrl =
        registration.active?.scriptURL ||
        registration.waiting?.scriptURL ||
        registration.installing?.scriptURL ||
        ""

      if (scriptUrl.includes("/firebase-messaging-sw.js")) {
        await registration.unregister()
      }
    }),
  )
}

function rememberWebPushEndpoint(subscription: PushSubscription) {
  localStorage.setItem(WEB_PUSH_ENDPOINT_STORAGE_KEY, subscription.endpoint)
}

function rememberWebPushEnabledState(enabled: boolean) {
  localStorage.setItem(WEB_PUSH_DISABLED_STORAGE_KEY, enabled ? "false" : "true")
}

async function registerCurrentDeviceWebPushSubscriptionInternal(): Promise<WebPushRegistrationResult> {
  if (!isWebPushSupported()) {
    return {
      status: "unsupported",
      message: "Bu cihaz Web Push bildirimlerini desteklemiyor.",
    }
  }

  await unregisterLegacyFirebaseMessagingServiceWorkers()

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

  rememberWebPushEndpoint(subscription)
  rememberWebPushEnabledState(true)

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

export async function deactivateCurrentDeviceWebPushSubscription() {
  if (!isWebPushSupported()) {
    rememberWebPushEnabledState(false)
    localStorage.removeItem(WEB_PUSH_ENDPOINT_STORAGE_KEY)
    return
  }

  const registrations = await navigator.serviceWorker.getRegistrations()
  const endpoints = new Set<string>()
  const subscriptions: PushSubscription[] = []

  await Promise.all(
    registrations.map(async (registration) => {
      const subscription = await registration.pushManager.getSubscription()

      if (subscription) {
        endpoints.add(subscription.endpoint)
        subscriptions.push(subscription)
      }
    }),
  )

  const storedEndpoint = localStorage.getItem(WEB_PUSH_ENDPOINT_STORAGE_KEY)

  if (storedEndpoint) {
    endpoints.add(storedEndpoint)
  }

  for (const endpoint of endpoints) {
    await apiRequest("/push/web/subscriptions/deactivate", {
      method: "POST",
      body: { endpoint },
      requiresAuth: true,
    })
  }

  await Promise.all(
    subscriptions.map(async (subscription) => {
      await subscription.unsubscribe()
    }),
  )

  await unregisterLegacyFirebaseMessagingServiceWorkers()

  rememberWebPushEnabledState(false)
  localStorage.removeItem(WEB_PUSH_ENDPOINT_STORAGE_KEY)
}
