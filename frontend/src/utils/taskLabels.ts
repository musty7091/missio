import type { TaskPriority, TaskStatus } from "../types/task"

export function getStatusLabel(status: TaskStatus) {
  if (status === "assigned") return "Bekliyor"
  if (status === "in_progress") return "Devam ediyor"
  if (status === "completed") return "Onay bekliyor"
  if (status === "approved") return "Onaylandı"
  if (status === "rejected") return "Reddedildi"
  if (status === "cancelled") return "İptal edildi"

  return status
}

export function getActionLabel(status: TaskStatus) {
  if (status === "assigned") return "Başlat"
  if (status === "in_progress") return "Tamamla"
  if (status === "completed") return "Detay"
  if (status === "approved") return "Detay"
  if (status === "rejected") return "Tekrar Gönder"
  if (status === "cancelled") return "Detay"

  return "Aç"
}

export function getPriorityLabel(priority: TaskPriority) {
  if (priority === "urgent") return "Acil"
  if (priority === "high") return "Yüksek"
  if (priority === "normal") return "Normal"
  if (priority === "low") return "Düşük"

  return priority
}
