type NavigatorWithAppBadge = Navigator & {
  setAppBadge?: (contents?: number) => Promise<void>
  clearAppBadge?: () => Promise<void>
}

async function sendClearBadgeMessageToServiceWorker(): Promise<void> {
  if (!("serviceWorker" in navigator)) {
    return
  }

  const controller = navigator.serviceWorker.controller

  if (controller) {
    controller.postMessage({
      type: "MISSIO_CLEAR_APP_BADGE",
    })
  }
}

export async function clearMissioAppBadge(): Promise<void> {
  const badgeNavigator = navigator as NavigatorWithAppBadge

  try {
    if (typeof badgeNavigator.clearAppBadge === "function") {
      await badgeNavigator.clearAppBadge()
    } else if (typeof badgeNavigator.setAppBadge === "function") {
      await badgeNavigator.setAppBadge(0)
    }
  } catch (error) {
    console.warn("MISSIO_APP_BADGE_CLEAR_FAILED", error)
  }

  await sendClearBadgeMessageToServiceWorker()
}

export function clearMissioAppBadgeWhenAppIsVisible(): void {
  const clearWhenVisible = () => {
    if (document.visibilityState === "visible") {
      void clearMissioAppBadge()
    }
  }

  window.addEventListener("focus", clearWhenVisible)
  document.addEventListener("visibilitychange", clearWhenVisible)

  void clearMissioAppBadge()
}
