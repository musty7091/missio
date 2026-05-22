import {
  AlertTriangle,
  BarChart3,
  Camera,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Clock3,
  FileCheck2,
  PlayCircle,
  ShieldAlert,
  ShieldCheck,
  UsersRound,
} from "lucide-react"
import type { ReactNode } from "react"
import type { TodayTask } from "../../types/task"
import { getPriorityLabel, getStatusLabel } from "../../utils/taskLabels"

type ReportsPanelProps = {
  tasks: TodayTask[]
  role: string
  onOpenTaskDetails: (task: TodayTask) => void
}

type ControlCheckStatus = "success" | "warning" | "info"

function isCompletedTask(task: TodayTask) {
  return task.status === "completed" || task.status === "approved"
}

function isOpenTask(task: TodayTask) {
  return (
    task.status !== "completed" &&
    task.status !== "approved" &&
    task.status !== "cancelled"
  )
}

function getPercent(value: number, total: number) {
  if (total <= 0) {
    return 0
  }

  return Math.round((value / total) * 100)
}

function MetricCard({
  title,
  value,
  description,
  icon,
}: {
  title: string
  value: string | number
  description: string
  icon: ReactNode
}) {
  return (
    <div className="rounded-[1.4rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[0.68rem] font-black uppercase tracking-[0.13em] text-[var(--missio-text-muted)]">
            {title}
          </p>

          <p className="mt-2 text-2xl font-black leading-none text-[var(--missio-text-main)]">
            {value}
          </p>

          <p className="mt-2 text-xs font-bold leading-5 text-[var(--missio-text-muted)]">
            {description}
          </p>
        </div>

        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
          {icon}
        </div>
      </div>
    </div>
  )
}

function getCheckStyles(status: ControlCheckStatus) {
  if (status === "success") {
    return {
      box: "border-emerald-200 bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950/30",
      icon: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200",
      text: "text-emerald-950 dark:text-emerald-100",
      muted: "text-emerald-800 dark:text-emerald-200",
    }
  }

  if (status === "warning") {
    return {
      box: "border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/30",
      icon: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-200",
      text: "text-amber-950 dark:text-amber-100",
      muted: "text-amber-800 dark:text-amber-200",
    }
  }

  return {
    box: "border-cyan-200 bg-cyan-50 dark:border-cyan-900 dark:bg-cyan-950/30",
    icon: "bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200",
    text: "text-cyan-950 dark:text-cyan-100",
    muted: "text-cyan-800 dark:text-cyan-200",
  }
}

function ControlCheckCard({
  status,
  icon,
  title,
  description,
}: {
  status: ControlCheckStatus
  icon: ReactNode
  title: string
  description: string
}) {
  const styles = getCheckStyles(status)

  return (
    <div className={`rounded-[1.4rem] border p-3 ${styles.box}`}>
      <div className="flex items-start gap-3">
        <div
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl ${styles.icon}`}
        >
          {icon}
        </div>

        <div className="min-w-0">
          <h3 className={`text-sm font-black ${styles.text}`}>{title}</h3>

          <p className={`mt-1 text-xs font-bold leading-5 ${styles.muted}`}>
            {description}
          </p>
        </div>
      </div>
    </div>
  )
}

function ControlTaskRow({
  task,
  onOpenTaskDetails,
}: {
  task: TodayTask
  onOpenTaskDetails: (task: TodayTask) => void
}) {
  return (
    <button
      type="button"
      onClick={() => onOpenTaskDetails(task)}
      className="flex w-full items-center justify-between gap-3 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-3 text-left transition active:scale-[0.99]"
    >
      <div className="min-w-0">
        <div className="mb-1.5 flex flex-wrap gap-1.5">
          <span
            className={
              task.taskType === "routine"
                ? "rounded-full bg-cyan-100 px-2 py-0.5 text-[0.6rem] font-black text-cyan-700 dark:bg-cyan-950 dark:text-cyan-200"
                : "rounded-full bg-violet-100 px-2 py-0.5 text-[0.6rem] font-black text-violet-700 dark:bg-violet-950 dark:text-violet-200"
            }
          >
            {task.taskType === "routine" ? "Rutin" : "Ekstra"}
          </span>

          <span className="rounded-full bg-[var(--missio-card-bg)] px-2 py-0.5 text-[0.6rem] font-black text-[var(--missio-text-muted)]">
            {getStatusLabel(task.status)}
          </span>

          <span className="rounded-full bg-[var(--missio-card-bg)] px-2 py-0.5 text-[0.6rem] font-black text-[var(--missio-text-muted)]">
            {getPriorityLabel(task.priority)}
          </span>
        </div>

        <p className="truncate text-sm font-black text-[var(--missio-text-main)]">
          {task.title}
        </p>

        <p className="mt-1 line-clamp-1 text-xs font-bold text-[var(--missio-text-muted)]">
          {task.description}
        </p>
      </div>

      <ChevronRight className="shrink-0 text-[var(--missio-text-muted)]" size={18} />
    </button>
  )
}

function StaffControlPanel({
  tasks,
  onOpenTaskDetails,
}: {
  tasks: TodayTask[]
  onOpenTaskDetails: (task: TodayTask) => void
}) {
  const totalCount = tasks.length
  const completedTasks = tasks.filter(isCompletedTask)
  const openTasks = tasks.filter(isOpenTask)
  const waitingTasks = tasks.filter((task) => task.status === "assigned")
  const activeTasks = tasks.filter((task) => task.status === "in_progress")
  const photoRequiredOpenTasks = tasks.filter(
    (task) => task.requiresPhoto && isOpenTask(task),
  )
  const approvalWaitingTasks = tasks.filter(
    (task) => task.status === "completed" && task.requiresManagerApproval,
  )

  const blockingTasks = [
    ...activeTasks,
    ...photoRequiredOpenTasks,
    ...waitingTasks,
  ].filter((task, index, list) => list.findIndex((item) => item.id === task.id) === index)

  const completionRate = getPercent(completedTasks.length, totalCount)
  const isReadyToClose =
    totalCount > 0 &&
    openTasks.length === 0 &&
    activeTasks.length === 0 &&
    photoRequiredOpenTasks.length === 0

  return (
    <section className="flex flex-1 flex-col pb-24">
      <div
        className={
          isReadyToClose
            ? "mb-4 rounded-[1.7rem] bg-emerald-950 p-4 text-white shadow-xl shadow-emerald-950/15"
            : "mb-4 rounded-[1.7rem] bg-slate-950 p-4 text-white shadow-xl shadow-slate-950/15"
        }
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-black text-cyan-200">
              <ShieldCheck size={14} />
              Kontrol
            </div>

            <h2 className="mt-3 text-2xl font-black leading-tight">
              {isReadyToClose ? "Bugün kapatılabilir" : "Eksik kontrolü"}
            </h2>

            <p className="mt-2 text-sm font-semibold leading-5 text-slate-300">
              Gün bitmeden açık, işlemde veya kanıt isteyen görevleri kontrol et.
            </p>
          </div>

          <div className="shrink-0 rounded-2xl bg-cyan-300 px-3 py-2 text-center text-slate-950">
            <p className="text-lg font-black leading-none">%{completionRate}</p>
            <p className="mt-1 text-[0.62rem] font-black">tamam</p>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-3 gap-2">
          <div className="rounded-2xl bg-white/10 px-3 py-2">
            <p className="text-xl font-black leading-none">{openTasks.length}</p>
            <p className="mt-1 text-[0.64rem] font-bold text-slate-300">Açık</p>
          </div>

          <div className="rounded-2xl bg-white/10 px-3 py-2">
            <p className="text-xl font-black leading-none">{activeTasks.length}</p>
            <p className="mt-1 text-[0.64rem] font-bold text-slate-300">İşlemde</p>
          </div>

          <div className="rounded-2xl bg-white/10 px-3 py-2">
            <p className="text-xl font-black leading-none">{photoRequiredOpenTasks.length}</p>
            <p className="mt-1 text-[0.64rem] font-bold text-slate-300">Kanıt</p>
          </div>
        </div>
      </div>

      {totalCount === 0 ? (
        <div className="flex flex-1 items-center justify-center rounded-[1.7rem] border border-dashed border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-6 text-center">
          <div>
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-3xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
              <ClipboardCheck size={28} />
            </div>

            <h3 className="mt-4 text-lg font-black">Kontrol edilecek görev yok</h3>

            <p className="mt-2 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
              Bugüne görev atandığında gün sonu kontrolün burada oluşacak.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-2.5">
            <ControlCheckCard
              status={openTasks.length === 0 ? "success" : "warning"}
              icon={
                openTasks.length === 0 ? (
                  <CheckCircle2 size={22} />
                ) : (
                  <AlertTriangle size={22} />
                )
              }
              title={
                openTasks.length === 0
                  ? "Açık görev kalmadı"
                  : `${openTasks.length} açık görev var`
              }
              description={
                openTasks.length === 0
                  ? "Bugünkü görevlerin tamamlanmış görünüyor."
                  : "Günü kapatmadan önce açık görevleri kontrol etmelisin."
              }
            />

            <ControlCheckCard
              status={activeTasks.length === 0 ? "success" : "warning"}
              icon={
                activeTasks.length === 0 ? (
                  <CheckCircle2 size={22} />
                ) : (
                  <PlayCircle size={22} />
                )
              }
              title={
                activeTasks.length === 0
                  ? "Devam eden görev yok"
                  : `${activeTasks.length} görev işlemde`
              }
              description={
                activeTasks.length === 0
                  ? "Yarım bırakılmış işlem görünmüyor."
                  : "Başlatılmış ama tamamlanmamış görev var."
              }
            />

            <ControlCheckCard
              status={photoRequiredOpenTasks.length === 0 ? "success" : "warning"}
              icon={
                photoRequiredOpenTasks.length === 0 ? (
                  <CheckCircle2 size={22} />
                ) : (
                  <Camera size={22} />
                )
              }
              title={
                photoRequiredOpenTasks.length === 0
                  ? "Eksik fotoğraf kanıtı görünmüyor"
                  : `${photoRequiredOpenTasks.length} görev fotoğraf kanıtı istiyor`
              }
              description={
                photoRequiredOpenTasks.length === 0
                  ? "Kanıt isteyen açık görev bulunmuyor."
                  : "Bu görevlerde fotoğraf kanıtı kontrol edilmeli."
              }
            />

            <ControlCheckCard
              status={approvalWaitingTasks.length === 0 ? "info" : "info"}
              icon={<FileCheck2 size={22} />}
              title={
                approvalWaitingTasks.length === 0
                  ? "Onay bekleyen görev yok"
                  : `${approvalWaitingTasks.length} görev yönetici onayında`
              }
              description={
                approvalWaitingTasks.length === 0
                  ? "Yönetici onayı bekleyen tamamlanmış görevin yok."
                  : "Bu görevler tamamlanmış, yönetici onayı bekliyor."
              }
            />
          </div>

          <div className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--missio-text-muted)]">
                  Hemen kontrol et
                </p>

                <h3 className="mt-1 text-base font-black text-[var(--missio-text-main)]">
                  Günü kapatmadan önce bakılacak işler
                </h3>
              </div>

              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-200">
                <ShieldAlert size={22} />
              </div>
            </div>

            {blockingTasks.length === 0 ? (
              <div className="rounded-2xl bg-emerald-50 p-3 text-sm font-bold text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-200">
                Kontrol gerektiren açık iş görünmüyor. Bugün kapatılabilir.
              </div>
            ) : (
              <div className="space-y-2">
                {blockingTasks.map((task) => (
                  <ControlTaskRow
                    key={task.id}
                    task={task}
                    onOpenTaskDetails={onOpenTaskDetails}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  )
}

function ManagementReportPlaceholder({ role }: { role: string }) {
  const roleTitle =
    role === "owner"
      ? "Patron raporları"
      : role === "admin"
        ? "Admin raporları"
        : "Yönetici raporları"

  return (
    <section className="flex flex-1 flex-col pb-24">
      <div className="mb-4 rounded-[1.7rem] bg-slate-950 p-4 text-white shadow-xl shadow-slate-950/15">
        <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-black text-cyan-200">
          <UsersRound size={14} />
          Raporlar
        </div>

        <h2 className="mt-3 text-2xl font-black leading-tight">{roleTitle}</h2>

        <p className="mt-2 text-sm font-semibold leading-5 text-slate-300">
          Bu ekran tüm personel ve işletme performansını göstermek için ayrıldı.
        </p>
      </div>

      <div className="space-y-3">
        <div className="rounded-[1.5rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-sm">
          <h3 className="text-base font-black text-[var(--missio-text-main)]">
            Yönetim raporu için backend adımı gerekli
          </h3>

          <p className="mt-2 text-sm font-bold leading-6 text-[var(--missio-text-muted)]">
            Şu an frontend yalnızca giriş yapan kullanıcının bugünkü görevlerini alıyor.
            Tüm personel raporu için ayrı rapor endpointleri ekleyeceğiz.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-2.5">
          <MetricCard
            title="Personel"
            value="Yakında"
            description="Kişi bazlı performans"
            icon={<UsersRound size={22} />}
          />

          <MetricCard
            title="Kanıt"
            value="Yakında"
            description="Fotoğraf uyumluluğu"
            icon={<Camera size={22} />}
          />

          <MetricCard
            title="Onay"
            value="Yakında"
            description="Onay / ret akışı"
            icon={<FileCheck2 size={22} />}
          />

          <MetricCard
            title="Risk"
            value="Yakında"
            description="Geciken ve eksik işler"
            icon={<AlertTriangle size={22} />}
          />
        </div>
      </div>
    </section>
  )
}

export function ReportsPanel({
  tasks,
  role,
  onOpenTaskDetails,
}: ReportsPanelProps) {
  if (role === "staff") {
    return <StaffControlPanel tasks={tasks} onOpenTaskDetails={onOpenTaskDetails} />
  }

  return <ManagementReportPlaceholder role={role} />
}
