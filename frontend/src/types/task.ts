export type ThemeMode = "light" | "dark"

export type TaskStatus =
  | "assigned"
  | "in_progress"
  | "completed"
  | "approved"
  | "rejected"
  | "cancelled"

export type TaskPriority = "low" | "normal" | "high" | "urgent"

export type TaskType = "routine" | "extra"

export type TodayTask = {
  id: number
  title: string
  description: string
  status: TaskStatus
  priority: TaskPriority
  taskType: TaskType
  taskDate: string
  time: string
  requiresPhoto: boolean
  requiresLocation: boolean
  requiresManagerApproval: boolean
}
