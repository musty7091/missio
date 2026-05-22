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
  assignedToUserId: number | null
  assignedToUserFullName: string | null
  assignedToUsername: string | null
  title: string
  description: string
  status: TaskStatus
  priority: TaskPriority
  taskType: TaskType
  taskDate: string
  time: string
  dueAtUtc: string | null
  assignedAtUtc: string | null
  startedAtUtc: string | null
  completedAtUtc: string | null
  approvedAtUtc: string | null
  createdAtUtc: string
  updatedAtUtc: string
  requiresPhoto: boolean
  requiresLocation: boolean
  requiresManagerApproval: boolean
}

