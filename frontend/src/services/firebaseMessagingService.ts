import { initializeApp } from "firebase/app"
import { getMessaging, getToken, isSupported, type Messaging } from "firebase/messaging"

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

let messagingInstance: Messaging | null = null

export async function isFirebaseMessagingSupported() {
  if (!("Notification" in window)) {
    return false
  }

  if (!("serviceWorker" in navigator)) {
    return false
  }

  return isSupported()
}

export async function getFirebaseMessagingInstance() {
  const supported = await isFirebaseMessagingSupported()

  if (!supported) {
    return null
  }

  if (messagingInstance) {
    return messagingInstance
  }

  const app = initializeApp(firebaseConfig)
  messagingInstance = getMessaging(app)

  return messagingInstance
}

export function getNotificationPermissionStatus() {
  if (!("Notification" in window)) {
    return "unsupported"
  }

  return Notification.permission
}

export async function requestMissioPushPermissionAndToken() {
  const supported = await isFirebaseMessagingSupported()

  if (!supported) {
    return {
      ok: false,
      reason: "unsupported",
      token: null,
      message: "Bu tarayıcı push bildirimlerini desteklemiyor.",
    }
  }

  const permission = await Notification.requestPermission()

  if (permission !== "granted") {
    return {
      ok: false,
      reason: permission,
      token: null,
      message: "Bildirim izni verilmedi.",
    }
  }

  const registration = await navigator.serviceWorker.register("/firebase-messaging-sw.js")
  const messaging = await getFirebaseMessagingInstance()

  if (!messaging) {
    return {
      ok: false,
      reason: "messaging_not_initialized",
      token: null,
      message: "Firebase Messaging başlatılamadı.",
    }
  }

  const vapidKey = import.meta.env.VITE_FIREBASE_VAPID_KEY

  if (!vapidKey) {
    return {
      ok: false,
      reason: "missing_vapid_key",
      token: null,
      message: "Firebase VAPID anahtarı bulunamadı.",
    }
  }

  const token = await getToken(messaging, {
    vapidKey,
    serviceWorkerRegistration: registration,
  })

  if (!token) {
    return {
      ok: false,
      reason: "empty_token",
      token: null,
      message: "Bildirim tokenı üretilemedi.",
    }
  }

  return {
    ok: true,
    reason: "granted",
    token,
    message: "Bildirim izni alındı.",
  }
}
