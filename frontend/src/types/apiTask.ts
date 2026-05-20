export type ApiTaskType = "routine" | "extra"

export type ApiTaskStatus =
  | "assigned"
  | "in_progress"
  | "completed"
  | "approved"
  | "rejected"
  | "cancelled"

export type ApiTaskPriority = "low" | "normal" | "high" | "urgent"

export type ApiTask = {
  id: number
  business_id: number
  template_id: number | null
  title: string
  description: string | null
  category_id: number | null
  assigned_to_user_id: number | null
  created_by_user_id: number | null
  task_type: ApiTaskType
  task_date: string
  priority: ApiTaskPriority
  status: ApiTaskStatus
  due_at_utc: string | null
  assigned_at_utc: string | null
  started_at_utc: string | null
  customer_arrived_at_utc: string | null
  completed_at_utc: string | null
  approved_at_utc: string | null
  requires_photo: boolean
  requires_location: boolean
  requires_manager_approval: boolean
  created_at_utc: string
  updated_at_utc: string
}

export type MyTodayTasksResponse = {
  task_date: string
  routine_tasks: ApiTask[]
  extra_tasks: ApiTask[]
}
