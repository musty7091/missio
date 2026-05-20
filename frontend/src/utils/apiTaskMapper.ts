import type { ApiTask } from "../types/apiTask"
import type { TodayTask } from "../types/task"

function formatTaskTime(task: ApiTask) {
  if (!task.due_at_utc) {
    return "Bugün"
  }

  const date = new Date(task.due_at_utc)

  if (Number.isNaN(date.getTime())) {
    return "Bugün"
  }

  return date.toLocaleTimeString("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
  })
}

export function mapApiTaskToTodayTask(task: ApiTask): TodayTask {
  return {
    id: task.id,
    title: task.title,
    description: task.description || "Açıklama eklenmemiş.",
    status: task.status,
    priority: task.priority,
    taskType: task.task_type,
    taskDate: task.task_date,
    time: formatTaskTime(task),
    requiresPhoto: task.requires_photo,
    requiresLocation: task.requires_location,
    requiresManagerApproval: task.requires_manager_approval,
  }
}

export function mapMyTodayTasksResponseToTodayTasks(response: {
  routine_tasks: ApiTask[]
  extra_tasks: ApiTask[]
}) {
  return [...response.routine_tasks, ...response.extra_tasks].map(mapApiTaskToTodayTask)
}
