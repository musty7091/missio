export type BrowserLocationPayload = {
  latitude: number
  longitude: number
  location_accuracy: number | null
}

export function isBrowserLocationSupported() {
  return typeof navigator !== "undefined" && "geolocation" in navigator
}

export function getBrowserLocationPayload(): Promise<BrowserLocationPayload> {
  return new Promise((resolve, reject) => {
    if (!isBrowserLocationSupported()) {
      reject(new Error("Bu cihazda konum desteği bulunamadı."))
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          location_accuracy: Number.isFinite(position.coords.accuracy)
            ? position.coords.accuracy
            : null,
        })
      },
      (error) => {
        if (error.code === error.PERMISSION_DENIED) {
          reject(
            new Error(
              "Konum izni kapalı. Lütfen tarayıcı veya uygulama ayarlarından konum iznini açın.",
            ),
          )
          return
        }

        if (error.code === error.POSITION_UNAVAILABLE) {
          reject(new Error("Konum bilgisi alınamadı. Lütfen internet ve GPS durumunu kontrol edin."))
          return
        }

        if (error.code === error.TIMEOUT) {
          reject(new Error("Konum alma işlemi zaman aşımına uğradı. Lütfen tekrar deneyin."))
          return
        }

        reject(new Error("Konum alınamadı. Lütfen cihaz konum ayarlarını kontrol edin."))
      },
      {
        enableHighAccuracy: true,
        timeout: 20000,
        maximumAge: 30000,
      },
    )
  })
}

export function mapLocationErrorToCode(error: unknown) {
  if (!(error instanceof Error)) {
    return "unknown_error"
  }

  const message = error.message.toLowerCase()

  if (message.includes("izin") || message.includes("permission")) {
    return "permission_denied"
  }

  if (message.includes("zaman") || message.includes("timeout")) {
    return "timeout"
  }

  if (message.includes("destek") || message.includes("support")) {
    return "not_supported"
  }

  return "location_unavailable"
}

export function getLocationErrorMessage(error: unknown) {
  if (error instanceof Error && error.message.trim()) {
    return error.message
  }

  return "Konum alınamadı."
}
