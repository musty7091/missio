import type { TodayTask } from "../types/task"

export const todayTasks: TodayTask[] = [
  {
    id: 1,
    title: "Reyon açılış kontrolü",
    description: "Raf düzeni, fiyat etiketleri ve eksik ürün kontrolü.",
    status: "assigned",
    priority: "high",
    time: "09:30",
    requiresPhoto: true,
    requiresLocation: true,
  },
  {
    id: 2,
    title: "Soğuk dolap sıcaklık kontrolü",
    description: "Dolap içi sıcaklık değerini kontrol edip fotoğraf ekle.",
    status: "in_progress",
    priority: "urgent",
    time: "10:15",
    requiresPhoto: true,
    requiresLocation: false,
  },
  {
    id: 3,
    title: "Günlük kasa çevresi temizliği",
    description: "Kasa önü, müşteri alanı ve ödeme noktasını kontrol et.",
    status: "completed",
    priority: "normal",
    time: "11:00",
    requiresPhoto: false,
    requiresLocation: false,
  },
]
