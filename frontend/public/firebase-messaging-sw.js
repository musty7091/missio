/* eslint-disable no-undef */

importScripts("https://www.gstatic.com/firebasejs/10.13.2/firebase-app-compat.js")
importScripts("https://www.gstatic.com/firebasejs/10.13.2/firebase-messaging-compat.js")

firebase.initializeApp({
  apiKey: "AIzaSyD6s1vM5DCjX-Js8Jqmr51O7SrkDFEmmUE",
  authDomain: "missio-cloud-cyprus.firebaseapp.com",
  projectId: "missio-cloud-cyprus",
  storageBucket: "missio-cloud-cyprus.firebasestorage.app",
  messagingSenderId: "913315393568",
  appId: "1:913315393568:web:a3d81281ca0c3702f38c45",
})

const messaging = firebase.messaging()

messaging.onBackgroundMessage((payload) => {
  const notificationTitle = payload.notification?.title || "Missio"
  const notificationOptions = {
    body: payload.notification?.body || "Yeni bildirimin var.",
    icon: "/missio-favicon-logo.png",
    badge: "/missio-favicon-logo.png",
    data: payload.data || {},
  }

  self.registration.showNotification(notificationTitle, notificationOptions)
})

self.addEventListener("notificationclick", (event) => {
  event.notification.close()

  const targetUrl = event.notification.data?.url || "/"

  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if ("focus" in client) {
          client.focus()
          return
        }
      }

      if (clients.openWindow) {
        return clients.openWindow(targetUrl)
      }

      return undefined
    }),
  )
})
