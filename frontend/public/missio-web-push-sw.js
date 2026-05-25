const MISSIO_DEFAULT_ICON = "/icons/icon-192x192.png"
const MISSIO_DEFAULT_BADGE_ICON = "/icons/icon-192x192.png"

function parsePushPayload(event) {
  if (!event.data) {
    return {}
  }

  try {
    return event.data.json()
  } catch (error) {
    try {
      return {
        title: "Missio",
        body: event.data.text(),
      }
    } catch (textError) {
      return {}
    }
  }
}

function resolveBadgeCount(payload) {
  const candidates = [
    payload.badgeCount,
    payload.badge_count,
    payload.openTaskCount,
    payload.open_task_count,
    payload.unreadCount,
    payload.unread_count,
    payload.data && payload.data.badgeCount,
    payload.data && payload.data.badge_count,
    payload.data && payload.data.openTaskCount,
    payload.data && payload.data.open_task_count,
    payload.data && payload.data.unreadCount,
    payload.data && payload.data.unread_count,
  ]

  for (const candidate of candidates) {
    const numberValue = Number(candidate)

    if (Number.isFinite(numberValue) && numberValue >= 0) {
      return Math.trunc(numberValue)
    }
  }

  return null
}

function shouldShowMissioNotification(payload) {
  if (payload.showNotification === false) {
    return false
  }

  if (payload.show_notification === false) {
    return false
  }

  if (payload.data && payload.data.showNotification === false) {
    return false
  }

  if (payload.data && payload.data.show_notification === false) {
    return false
  }

  return true
}

async function setMissioAppBadge(count) {
  const numberValue = Number(count)

  if (!Number.isFinite(numberValue) || numberValue <= 0) {
    await clearMissioAppBadge()
    return
  }

  const safeCount = Math.trunc(numberValue)

  try {
    if (self.navigator && typeof self.navigator.setAppBadge === "function") {
      await self.navigator.setAppBadge(safeCount)
    }
  } catch (error) {
    console.warn("MISSIO_APP_BADGE_SET_FAILED", error)
  }
}

async function clearMissioAppBadge() {
  try {
    if (self.navigator && typeof self.navigator.clearAppBadge === "function") {
      await self.navigator.clearAppBadge()
      return
    }

    if (self.navigator && typeof self.navigator.setAppBadge === "function") {
      await self.navigator.setAppBadge(0)
    }
  } catch (error) {
    console.warn("MISSIO_APP_BADGE_CLEAR_FAILED", error)
  }
}

self.addEventListener("push", (event) => {
  const payload = parsePushPayload(event)

  const title = payload.title || "Missio"
  const resolvedBadgeCount = resolveBadgeCount(payload)
  const badgeCount = resolvedBadgeCount === null ? 1 : resolvedBadgeCount
  const showNotification = shouldShowMissioNotification(payload)

  if (!showNotification) {
    event.waitUntil(setMissioAppBadge(badgeCount))
    return
  }

  const notificationOptions = {
    body: payload.body || "Yeni bir Missio bildirimin var.",
    icon: payload.icon || MISSIO_DEFAULT_ICON,
    badge: payload.badge || MISSIO_DEFAULT_BADGE_ICON,
    tag: payload.tag || "missio-notification",
    renotify: true,
    silent: false,
    requireInteraction: false,
    data: {
      url: payload.url || "/",
      ...(payload.data || {}),
    },
  }

  event.waitUntil(
    Promise.all([
      self.registration.showNotification(title, notificationOptions),
      setMissioAppBadge(badgeCount),
    ]),
  )
})

self.addEventListener("notificationclick", (event) => {
  event.notification.close()

  const targetUrl = event.notification.data && event.notification.data.url
    ? event.notification.data.url
    : "/"

  event.waitUntil(
    (async () => {
      await clearMissioAppBadge()

      const windowClients = await clients.matchAll({
        type: "window",
        includeUncontrolled: true,
      })

      for (const client of windowClients) {
        if ("focus" in client) {
          await client.focus()

          if ("navigate" in client) {
            await client.navigate(targetUrl)
          }

          return
        }
      }

      if (clients.openWindow) {
        await clients.openWindow(targetUrl)
      }
    })(),
  )
})

self.addEventListener("message", (event) => {
  if (!event.data || event.data.type !== "MISSIO_CLEAR_APP_BADGE") {
    return
  }

  event.waitUntil(clearMissioAppBadge())
})