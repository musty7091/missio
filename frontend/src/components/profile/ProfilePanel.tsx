import {
  AlertCircle,
  BadgeCheck,
  Building2,
  Camera,
  ChevronDown,
  ChevronUp,
  Clock3,
  KeyRound,
  LockKeyhole,
  LogOut,
  Mail,
  Moon,
  Pencil,
  Power,
  PowerOff,
  RefreshCw,
  RotateCcw,
  Save,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Smartphone,
  Sun,
  UserPlus,
  UserRound,
  UsersRound,
  X,
} from "lucide-react"
import { useEffect, useMemo, useState, type ReactNode } from "react"
import {
  changeBusinessUserRole,
  createBusinessUser,
  listBusinessUsers,
  resetBusinessUserPassword,
  setBusinessUserActiveStatus,
  updateBusinessUser,
  type BusinessUser,
  type BusinessUserRole,
} from "../../services/businessUserService"
import {
  deactivateCurrentWebPushSubscription,
  isWebPushLocallyEnabled,
  requestMissioWebPushPermissionAndSubscribe,
  sendCurrentUserWebPushTest,
} from "../../services/webPushNotificationService"
import { changeOwnPassword } from "../../services/profileSecurityService"
import type { UserMeResponse } from "../../types/auth"
import type { ThemeMode } from "../../types/task"

type ProfilePanelProps = {
  user: UserMeResponse
  theme: ThemeMode
  onToggleTheme: () => void
  onLogout: () => void
}

type InfoRowProps = {
  icon: ReactNode
  label: string
  value: string
}

type UserManagementPanelProps = {
  currentUser: UserMeResponse
}

type CreateUserFormState = {
  full_name: string
  username: string
  password: string
  role: BusinessUserRole
  email: string
}

type EditUserFormState = {
  full_name: string
  email: string
  is_active: boolean
}

type UserRoleFilter = "all" | "boss" | "manager" | "staff"
type UserStatusFilter = "all" | "active" | "passive"

type PasswordFormState = {
  current_password: string
  new_password: string
  new_password_repeat: string
}

const emptyCreateForm: CreateUserFormState = {
  full_name: "",
  username: "",
  password: "",
  role: "staff",
  email: "",
}

const emptyPasswordForm: PasswordFormState = {
  current_password: "",
  new_password: "",
  new_password_repeat: "",
}

function getRoleLabel(role: string) {
  if (role === "boss") {
    return "Patron"
  }

  if (role === "super_admin") {
    return "Süper Admin"
  }

  if (role === "manager") {
    return "Manager"
  }

  if (role === "staff") {
    return "Personel"
  }

  return role
}

function getInitials(fullName: string) {
  const words = fullName
    .trim()
    .split(" ")
    .filter(Boolean)

  if (words.length === 0) {
    return "M"
  }

  if (words.length === 1) {
    return words[0].slice(0, 2).toUpperCase()
  }

  return `${words[0][0]}${words[words.length - 1][0]}`.toUpperCase()
}

function getAllowedCreateRoles(currentRole: string): BusinessUserRole[] {
  if (currentRole === "super_admin") {
    return ["boss", "manager", "staff"]
  }

  if (currentRole === "boss") {
    return ["manager", "staff"]
  }

  return []
}

function canShowUserManagement(user: UserMeResponse) {
  return user.business_id !== null && (user.role === "super_admin" || user.role === "boss")
}

function canEditTargetUser(currentUser: UserMeResponse, targetUser: BusinessUser) {
  if (currentUser.role === "super_admin") {
    return true
  }

  if (currentUser.role === "boss") {
    return targetUser.role === "manager" || targetUser.role === "staff"
  }

  return false
}

function canChangeTargetRole(currentUser: UserMeResponse, targetUser: BusinessUser) {
  if (currentUser.id === targetUser.id) {
    return false
  }

  if (targetUser.role !== "manager" && targetUser.role !== "staff") {
    return false
  }

  return currentUser.role === "super_admin" || currentUser.role === "boss"
}

function getActiveLabel(isActive: boolean) {
  return isActive ? "Aktif" : "Pasif"
}

function normalizeOptionalEmail(value: string) {
  const normalizedValue = value.trim().toLowerCase()

  if (!normalizedValue) {
    return null
  }

  return normalizedValue
}

function InfoRow({ icon, label, value }: InfoRowProps) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
        {icon}
      </div>

      <div className="min-w-0">
        <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--missio-text-muted)]">
          {label}
        </p>
        <p className="mt-1 truncate text-sm font-black text-[var(--missio-text-main)]">
          {value}
        </p>
      </div>
    </div>
  )
}

function UserManagementPanel({ currentUser }: UserManagementPanelProps) {
  const [users, setUsers] = useState<BusinessUser[]>([])
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [createForm, setCreateForm] = useState<CreateUserFormState>(emptyCreateForm)
  const [editForm, setEditForm] = useState<EditUserFormState>({
    full_name: "",
    email: "",
    is_active: true,
  })
  const [resetPasswordValue, setResetPasswordValue] = useState("")
  const [isManagementOpen, setIsManagementOpen] = useState(false)
  const [isCreateFormOpen, setIsCreateFormOpen] = useState(false)
  const [isEditPanelOpen, setIsEditPanelOpen] = useState(false)
  const [searchText, setSearchText] = useState("")
  const [roleFilter, setRoleFilter] = useState<UserRoleFilter>("all")
  const [statusFilter, setStatusFilter] = useState<UserStatusFilter>("all")
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const allowedCreateRoles = useMemo(
    () => getAllowedCreateRoles(currentUser.role),
    [currentUser.role],
  )

  const selectedUser = useMemo(() => {
    if (selectedUserId === null) {
      return null
    }

    return users.find((user) => user.id === selectedUserId) ?? null
  }, [selectedUserId, users])

  const userStats = useMemo(() => {
    const activeCount = users.filter((user) => user.is_active).length
    const passiveCount = users.length - activeCount
    const managerCount = users.filter((user) => user.role === "manager").length
    const staffCount = users.filter((user) => user.role === "staff").length

    return {
      totalCount: users.length,
      activeCount,
      passiveCount,
      managerCount,
      staffCount,
    }
  }, [users])

  const filteredUsers = useMemo(() => {
    const normalizedSearch = searchText.trim().toLowerCase()

    return users.filter((businessUser) => {
      const matchesSearch =
        !normalizedSearch ||
        businessUser.full_name.toLowerCase().includes(normalizedSearch) ||
        businessUser.username.toLowerCase().includes(normalizedSearch) ||
        (businessUser.email ?? "").toLowerCase().includes(normalizedSearch)

      const matchesRole = roleFilter === "all" || businessUser.role === roleFilter

      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "active" && businessUser.is_active) ||
        (statusFilter === "passive" && !businessUser.is_active)

      return matchesSearch && matchesRole && matchesStatus
    })
  }, [users, searchText, roleFilter, statusFilter])

  async function loadUsers() {
    if (currentUser.business_id === null) {
      return
    }

    setIsLoading(true)
    setErrorMessage(null)

    try {
      const response = await listBusinessUsers(currentUser.business_id)
      setUsers(response)

      if (selectedUserId !== null && !response.some((user) => user.id === selectedUserId)) {
        setSelectedUserId(null)
        setIsEditPanelOpen(false)
      }
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Kullanıcı listesi alınamadı.")
      }
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadUsers()
  }, [currentUser.business_id])

  useEffect(() => {
    if (!selectedUser) {
      setEditForm({
        full_name: "",
        email: "",
        is_active: true,
      })
      setResetPasswordValue("")
      return
    }

    setEditForm({
      full_name: selectedUser.full_name,
      email: selectedUser.email ?? "",
      is_active: selectedUser.is_active,
    })
    setResetPasswordValue("")
  }, [selectedUser])

  function handleOpenUserForEdit(businessUser: BusinessUser) {
    setSelectedUserId(businessUser.id)
    setIsEditPanelOpen(true)
    setMessage(null)
    setErrorMessage(null)
  }

  function handleCloseEditPanel() {
    setSelectedUserId(null)
    setIsEditPanelOpen(false)
    setResetPasswordValue("")
  }

  async function handleCreateUser() {
    if (currentUser.business_id === null) {
      return
    }

    setIsSaving(true)
    setMessage(null)
    setErrorMessage(null)

    try {
      const response = await createBusinessUser(currentUser.business_id, {
        full_name: createForm.full_name.trim(),
        username: createForm.username.trim().toLowerCase(),
        password: createForm.password.trim(),
        role: createForm.role,
        email: normalizeOptionalEmail(createForm.email),
        theme_preference: null,
      })

      setMessage(response.message)
      setCreateForm(emptyCreateForm)
      setIsCreateFormOpen(false)
      await loadUsers()
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Kullanıcı oluşturulamadı.")
      }
    } finally {
      setIsSaving(false)
    }
  }

  async function handleUpdateUser() {
    if (currentUser.business_id === null || selectedUser === null) {
      return
    }

    setIsSaving(true)
    setMessage(null)
    setErrorMessage(null)

    try {
      const response = await updateBusinessUser(currentUser.business_id, selectedUser.id, {
        full_name: editForm.full_name.trim(),
        email: normalizeOptionalEmail(editForm.email),
        is_active: editForm.is_active,
      })

      setMessage(response.message)
      setUsers((currentUsers) =>
        currentUsers.map((user) => (user.id === response.user.id ? response.user : user)),
      )
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Kullanıcı güncellenemedi.")
      }
    } finally {
      setIsSaving(false)
    }
  }

  async function handleToggleActiveStatus(targetUser: BusinessUser) {
    if (currentUser.business_id === null) {
      return
    }

    if (targetUser.id === currentUser.id) {
      setErrorMessage("Kendi kullanıcınızı pasif hale getiremezsiniz.")
      return
    }

    setIsSaving(true)
    setMessage(null)
    setErrorMessage(null)

    try {
      const response = await setBusinessUserActiveStatus(
        currentUser.business_id,
        targetUser.id,
        !targetUser.is_active,
      )

      setMessage(response.message)
      setUsers((currentUsers) =>
        currentUsers.map((user) => (user.id === response.user.id ? response.user : user)),
      )
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Kullanıcı durumu değiştirilemedi.")
      }
    } finally {
      setIsSaving(false)
    }
  }

  async function handleResetPassword() {
    if (currentUser.business_id === null || selectedUser === null) {
      return
    }

    setIsSaving(true)
    setMessage(null)
    setErrorMessage(null)

    try {
      const response = await resetBusinessUserPassword(
        currentUser.business_id,
        selectedUser.id,
        {
          new_password: resetPasswordValue.trim(),
        },
      )

      setMessage(response.message)
      setResetPasswordValue("")
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Şifre sıfırlanamadı.")
      }
    } finally {
      setIsSaving(false)
    }
  }

  async function handleChangeRole(targetUser: BusinessUser, role: "manager" | "staff") {
    if (currentUser.business_id === null) {
      return
    }

    setIsSaving(true)
    setMessage(null)
    setErrorMessage(null)

    try {
      const response = await changeBusinessUserRole(currentUser.business_id, targetUser.id, {
        role,
      })

      setMessage(response.message)
      setUsers((currentUsers) =>
        currentUsers.map((user) => (user.id === response.user.id ? response.user : user)),
      )
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Rol değiştirilemedi.")
      }
    } finally {
      setIsSaving(false)
    }
  }

  if (currentUser.business_id === null) {
    return (
      <div className="rounded-[2rem] border border-amber-200 bg-amber-50 p-4 text-amber-800 shadow-xl shadow-slate-900/5 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100">
        <div className="flex items-start gap-3">
          <AlertCircle size={22} />
          <div>
            <h3 className="text-base font-black">Kullanıcı yönetimi açılamadı</h3>
            <p className="mt-1 text-sm font-semibold leading-6">
              Bu hesap bir işletmeye bağlı görünmüyor. Kullanıcı yönetimi için business_id gerekli.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-xl shadow-slate-900/5">
      <div className="flex items-start gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
          <UsersRound size={22} />
        </div>

        <div className="min-w-0 flex-1">
          <h3 className="text-lg font-black tracking-tight">Kullanıcı Yönetimi</h3>
          <p className="mt-1 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
            Kullanıcı oluşturma, düzenleme, aktif-pasif ve şifre sıfırlama işlemleri.
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            <span className="rounded-full bg-[var(--missio-primary-soft)] px-3 py-1 text-xs font-black text-cyan-700 dark:text-cyan-200">
              {userStats.totalCount} kullanıcı
            </span>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-black text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200">
              {userStats.activeCount} aktif
            </span>
            <span className="rounded-full bg-red-50 px-3 py-1 text-xs font-black text-red-700 dark:bg-red-950 dark:text-red-200">
              {userStats.passiveCount} pasif
            </span>
          </div>
        </div>
      </div>

      {message && (
        <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
          {message}
        </div>
      )}

      {errorMessage && (
        <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          {errorMessage}
        </div>
      )}

      <div className="mt-4 grid grid-cols-2 gap-3">
        <button
          type="button"
          onClick={() => setIsManagementOpen((currentValue) => !currentValue)}
          className="flex items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 py-3 text-sm font-black text-white shadow-lg shadow-teal-500/20 transition active:scale-95"
        >
          {isManagementOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          {isManagementOpen ? "Yönetimi kapat" : "Yönetimi aç"}
        </button>

        <button
          type="button"
          onClick={() => void loadUsers()}
          disabled={isLoading || isSaving}
          className="flex items-center justify-center gap-2 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3 text-sm font-black text-[var(--missio-text-main)] transition active:scale-95 disabled:opacity-50"
        >
          <RefreshCw size={18} />
          Yenile
        </button>
      </div>

      {isManagementOpen && (
        <div className="mt-5 space-y-4">
          <div className="rounded-3xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-4">
            <div className="flex items-center gap-2">
              <SlidersHorizontal size={18} />
              <h4 className="text-base font-black">Arama ve filtre</h4>
            </div>

            <div className="mt-4 grid gap-3">
              <div className="relative">
                <Search
                  size={17}
                  className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[var(--missio-text-muted)]"
                />
                <input
                  value={searchText}
                  onChange={(event) => setSearchText(event.target.value)}
                  placeholder="Ad, kullanıcı adı veya e-posta ara"
                  className="w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] py-3 pl-11 pr-4 text-sm font-bold outline-none focus:border-cyan-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <select
                  value={roleFilter}
                  onChange={(event) => setRoleFilter(event.target.value as UserRoleFilter)}
                  className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3 text-sm font-black outline-none focus:border-cyan-400"
                >
                  <option value="all">Tüm roller</option>
                  <option value="boss">Patron</option>
                  <option value="manager">Manager</option>
                  <option value="staff">Personel</option>
                </select>

                <select
                  value={statusFilter}
                  onChange={(event) =>
                    setStatusFilter(event.target.value as UserStatusFilter)
                  }
                  className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3 text-sm font-black outline-none focus:border-cyan-400"
                >
                  <option value="all">Tüm durumlar</option>
                  <option value="active">Aktif</option>
                  <option value="passive">Pasif</option>
                </select>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-4">
            <button
              type="button"
              onClick={() => setIsCreateFormOpen((currentValue) => !currentValue)}
              disabled={allowedCreateRoles.length === 0}
              className="flex w-full items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 py-3 text-sm font-black text-white shadow-lg shadow-teal-500/20 transition active:scale-95 disabled:opacity-50"
            >
              {isCreateFormOpen ? <X size={18} /> : <UserPlus size={18} />}
              {isCreateFormOpen ? "Yeni kullanıcı formunu kapat" : "Yeni kullanıcı oluştur"}
            </button>

            {isCreateFormOpen && (
              <div className="mt-4 grid gap-3">
                <input
                  value={createForm.full_name}
                  onChange={(event) =>
                    setCreateForm((currentForm) => ({
                      ...currentForm,
                      full_name: event.target.value,
                    }))
                  }
                  placeholder="Ad soyad"
                  className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3 text-sm font-bold outline-none focus:border-cyan-400"
                />

                <input
                  value={createForm.username}
                  onChange={(event) =>
                    setCreateForm((currentForm) => ({
                      ...currentForm,
                      username: event.target.value,
                    }))
                  }
                  placeholder="Kullanıcı adı"
                  className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3 text-sm font-bold outline-none focus:border-cyan-400"
                />

                <input
                  value={createForm.email}
                  onChange={(event) =>
                    setCreateForm((currentForm) => ({
                      ...currentForm,
                      email: event.target.value,
                    }))
                  }
                  placeholder="E-posta / isteğe bağlı"
                  className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3 text-sm font-bold outline-none focus:border-cyan-400"
                />

                <input
                  value={createForm.password}
                  onChange={(event) =>
                    setCreateForm((currentForm) => ({
                      ...currentForm,
                      password: event.target.value,
                    }))
                  }
                  placeholder="Geçici şifre"
                  type="password"
                  className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3 text-sm font-bold outline-none focus:border-cyan-400"
                />

                <select
                  value={createForm.role}
                  onChange={(event) =>
                    setCreateForm((currentForm) => ({
                      ...currentForm,
                      role: event.target.value as BusinessUserRole,
                    }))
                  }
                  className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3 text-sm font-black outline-none focus:border-cyan-400"
                >
                  {allowedCreateRoles.map((role) => (
                    <option key={role} value={role}>
                      {getRoleLabel(role)}
                    </option>
                  ))}
                </select>

                <button
                  type="button"
                  onClick={() => void handleCreateUser()}
                  disabled={isSaving || allowedCreateRoles.length === 0}
                  className="flex items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 py-3 text-sm font-black text-white shadow-lg shadow-teal-500/20 transition active:scale-95 disabled:opacity-50"
                >
                  <UserPlus size={18} />
                  Kullanıcıyı kaydet
                </button>
              </div>
            )}
          </div>

          <div className="rounded-3xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-4">
            <div className="flex items-center justify-between gap-3">
              <h4 className="text-base font-black">Kullanıcı listesi</h4>
              <span className="rounded-full bg-[var(--missio-primary-soft)] px-3 py-1 text-xs font-black text-cyan-700 dark:text-cyan-200">
                {filteredUsers.length} gösteriliyor
              </span>
            </div>

            <div className="mt-3 max-h-[28rem] space-y-2 overflow-y-auto pr-1">
              {isLoading && (
                <div className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-4 text-sm font-bold text-[var(--missio-text-muted)]">
                  Kullanıcılar yükleniyor...
                </div>
              )}

              {!isLoading && filteredUsers.length === 0 && (
                <div className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-4 text-sm font-bold text-[var(--missio-text-muted)]">
                  Bu filtreye uygun kullanıcı bulunamadı.
                </div>
              )}

              {!isLoading &&
                filteredUsers.map((businessUser) => {
                  const isSelected = selectedUserId === businessUser.id
                  const canEdit = canEditTargetUser(currentUser, businessUser)
                  const canChangeRole = canChangeTargetRole(currentUser, businessUser)

                  return (
                    <div
                      key={businessUser.id}
                      className={
                        isSelected
                          ? "rounded-2xl border border-cyan-300 bg-cyan-50 p-3 dark:border-cyan-800 dark:bg-cyan-950/40"
                          : "rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3"
                      }
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <h5 className="truncate text-sm font-black text-[var(--missio-text-main)]">
                              {businessUser.full_name}
                            </h5>

                            <span
                              className={
                                businessUser.is_active
                                  ? "shrink-0 rounded-full bg-emerald-50 px-2 py-0.5 text-[0.62rem] font-black text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200"
                                  : "shrink-0 rounded-full bg-red-50 px-2 py-0.5 text-[0.62rem] font-black text-red-700 dark:bg-red-950 dark:text-red-200"
                              }
                            >
                              {getActiveLabel(businessUser.is_active)}
                            </span>
                          </div>

                          <p className="mt-1 truncate text-xs font-bold text-[var(--missio-text-muted)]">
                            @{businessUser.username} · {getRoleLabel(businessUser.role)}
                          </p>
                        </div>

                        <button
                          type="button"
                          onClick={() => handleOpenUserForEdit(businessUser)}
                          disabled={!canEdit}
                          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] text-[var(--missio-text-main)] transition active:scale-95 disabled:opacity-40"
                          title="Düzenle"
                        >
                          <Pencil size={17} />
                        </button>
                      </div>

                      <div className="mt-2 grid grid-cols-2 gap-2">
                        <button
                          type="button"
                          onClick={() => void handleToggleActiveStatus(businessUser)}
                          disabled={!canEdit || businessUser.id === currentUser.id || isSaving}
                          className={
                            businessUser.is_active
                              ? "flex items-center justify-center gap-1.5 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-black text-red-700 transition active:scale-95 disabled:opacity-40 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
                              : "flex items-center justify-center gap-1.5 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-black text-emerald-700 transition active:scale-95 disabled:opacity-40 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200"
                          }
                        >
                          {businessUser.is_active ? <PowerOff size={14} /> : <Power size={14} />}
                          {businessUser.is_active ? "Pasife al" : "Aktif yap"}
                        </button>

                        {canChangeRole ? (
                          <select
                            value={businessUser.role}
                            onChange={(event) => {
                              const newRole = event.target.value

                              if (newRole === "manager" || newRole === "staff") {
                                void handleChangeRole(businessUser, newRole)
                              }
                            }}
                            disabled={isSaving}
                            className="rounded-xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 py-2 text-xs font-black outline-none focus:border-cyan-400 disabled:opacity-50"
                          >
                            <option value="manager">Manager</option>
                            <option value="staff">Personel</option>
                          </select>
                        ) : (
                          <div className="flex items-center justify-center rounded-xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 py-2 text-xs font-black text-[var(--missio-text-muted)]">
                            Rol kilitli
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
            </div>
          </div>

          {isEditPanelOpen && selectedUser && (
            <div className="rounded-3xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <Pencil size={18} />
                    <h4 className="text-base font-black">Kullanıcı düzenle</h4>
                  </div>

                  <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
                    {selectedUser.username} · {getRoleLabel(selectedUser.role)}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleCloseEditPanel}
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] text-[var(--missio-text-main)] transition active:scale-95"
                >
                  <X size={16} />
                </button>
              </div>

              <div className="mt-4 grid gap-3">
                <input
                  value={editForm.full_name}
                  onChange={(event) =>
                    setEditForm((currentForm) => ({
                      ...currentForm,
                      full_name: event.target.value,
                    }))
                  }
                  placeholder="Ad soyad"
                  className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3 text-sm font-bold outline-none focus:border-cyan-400"
                />

                <input
                  value={editForm.email}
                  onChange={(event) =>
                    setEditForm((currentForm) => ({
                      ...currentForm,
                      email: event.target.value,
                    }))
                  }
                  placeholder="E-posta / isteğe bağlı"
                  className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3 text-sm font-bold outline-none focus:border-cyan-400"
                />

                <label className="flex items-center justify-between gap-3 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3">
                  <span className="text-sm font-black">Hesap aktif mi?</span>
                  <input
                    type="checkbox"
                    checked={editForm.is_active}
                    disabled={selectedUser.id === currentUser.id}
                    onChange={(event) =>
                      setEditForm((currentForm) => ({
                        ...currentForm,
                        is_active: event.target.checked,
                      }))
                    }
                    className="h-5 w-5 accent-cyan-500 disabled:opacity-40"
                  />
                </label>

                <button
                  type="button"
                  onClick={() => void handleUpdateUser()}
                  disabled={isSaving}
                  className="flex items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 py-3 text-sm font-black text-white shadow-lg shadow-teal-500/20 transition active:scale-95 disabled:opacity-50"
                >
                  <Save size={18} />
                  Değişiklikleri kaydet
                </button>
              </div>

              <div className="mt-5 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4">
                <div className="flex items-center gap-2">
                  <RotateCcw size={17} />
                  <h5 className="text-sm font-black">Şifre sıfırla</h5>
                </div>

                <div className="mt-3 grid gap-3">
                  <input
                    value={resetPasswordValue}
                    onChange={(event) => setResetPasswordValue(event.target.value)}
                    placeholder="Yeni geçici şifre"
                    type="password"
                    className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3 text-sm font-bold outline-none focus:border-cyan-400"
                  />

                  <button
                    type="button"
                    onClick={() => void handleResetPassword()}
                    disabled={isSaving}
                    className="flex items-center justify-center gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-black text-amber-700 transition active:scale-95 disabled:opacity-50 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200"
                  >
                    <KeyRound size={18} />
                    Şifreyi sıfırla
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function ProfilePanel({ user, theme, onToggleTheme, onLogout }: ProfilePanelProps) {
  const emailValue = user.email && user.email.trim() ? user.email : "E-posta tanımlı değil"
  const initials = getInitials(user.full_name)
  const [isRequestingPushPermission, setIsRequestingPushPermission] = useState(false)
  const [pushStatusMessage, setPushStatusMessage] = useState<string | null>(null)
  const [pushErrorMessage, setPushErrorMessage] = useState<string | null>(null)
  const [isPushEnabled, setIsPushEnabled] = useState(
    () => isWebPushLocallyEnabled(),
  )
  const [isSendingPushTest, setIsSendingPushTest] = useState(false)
  const [passwordForm, setPasswordForm] = useState<PasswordFormState>(emptyPasswordForm)
  const [isChangingPassword, setIsChangingPassword] = useState(false)
  const [passwordStatusMessage, setPasswordStatusMessage] = useState<string | null>(null)
  const [passwordErrorMessage, setPasswordErrorMessage] = useState<string | null>(null)

  function rememberPushEnabledState(enabled: boolean) {
    localStorage.setItem(
      "missio-web-push-notifications-disabled",
      enabled ? "false" : "true",
    )
  }

  async function handleEnablePushNotifications() {
    setIsRequestingPushPermission(true)
    setPushStatusMessage(null)
    setPushErrorMessage(null)

    try {
      const result = await requestMissioWebPushPermissionAndSubscribe()

      if (!result.ok) {
        setIsPushEnabled(false)
        setPushErrorMessage(result.message)
        return
      }

      rememberPushEnabledState(true)
      setIsPushEnabled(true)
      setPushStatusMessage(result.message)
    } catch (error) {
      setIsPushEnabled(false)

      if (error instanceof Error) {
        setPushErrorMessage(error.message)
      } else {
        setPushErrorMessage("Web Push bildirimleri açılamadı.")
      }
    } finally {
      setIsRequestingPushPermission(false)
    }
  }

  async function handleDisablePushNotifications() {
    setIsRequestingPushPermission(true)
    setPushStatusMessage(null)
    setPushErrorMessage(null)

    try {
      const result = await deactivateCurrentWebPushSubscription()

      rememberPushEnabledState(false)
      setIsPushEnabled(false)
      setPushStatusMessage(result.message)
    } catch (error) {
      if (error instanceof Error) {
        setPushErrorMessage(error.message)
      } else {
        setPushErrorMessage("Web Push bildirimleri kapatılamadı.")
      }
    } finally {
      setIsRequestingPushPermission(false)
    }
  }

  async function handleTogglePushNotifications() {
    if (isPushEnabled) {
      await handleDisablePushNotifications()
      return
    }

    await handleEnablePushNotifications()
  }

  async function handleSendWebPushTest() {
    setIsSendingPushTest(true)
    setPushStatusMessage(null)
    setPushErrorMessage(null)

    try {
      const response = await sendCurrentUserWebPushTest()

      setPushStatusMessage(
        `${response.message} Gönderilen: ${response.sent_count}, Başarısız: ${response.failed_count}.`,
      )
    } catch (error) {
      if (error instanceof Error) {
        setPushErrorMessage(error.message)
      } else {
        setPushErrorMessage("Web Push test bildirimi gönderilemedi.")
      }
    } finally {
      setIsSendingPushTest(false)
    }
  }


  async function handleChangeOwnPassword() {
    const currentPassword = passwordForm.current_password.trim()
    const newPassword = passwordForm.new_password.trim()
    const newPasswordRepeat = passwordForm.new_password_repeat.trim()

    setPasswordStatusMessage(null)
    setPasswordErrorMessage(null)

    if (!currentPassword || !newPassword || !newPasswordRepeat) {
      setPasswordErrorMessage("Mevcut şifre, yeni şifre ve tekrar alanları zorunludur.")
      return
    }

    if (newPassword !== newPasswordRepeat) {
      setPasswordErrorMessage("Yeni şifre ve yeni şifre tekrarı eşleşmiyor.")
      return
    }

    if (currentPassword === newPassword) {
      setPasswordErrorMessage("Yeni şifre mevcut şifre ile aynı olamaz.")
      return
    }

    setIsChangingPassword(true)

    try {
      const response = await changeOwnPassword({
        current_password: currentPassword,
        new_password: newPassword,
        new_password_repeat: newPasswordRepeat,
      })

      setPasswordStatusMessage(response.message)
      setPasswordForm(emptyPasswordForm)
    } catch (error) {
      if (error instanceof Error) {
        setPasswordErrorMessage(error.message)
      } else {
        setPasswordErrorMessage("Şifre değiştirilemedi.")
      }
    } finally {
      setIsChangingPassword(false)
    }
  }


  return (
    <section className="flex flex-1 flex-col gap-4 pb-24">
      <div className="overflow-hidden rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] shadow-xl shadow-slate-900/5">
        <div className="relative bg-slate-950 p-5 text-white">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(34,211,238,0.24),transparent_34%),linear-gradient(135deg,rgba(15,23,42,1),rgba(2,6,23,1))]" />
          <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full border border-cyan-300/20" />

          <div className="relative flex items-center gap-4">
            <div className="relative flex h-16 w-16 shrink-0 items-center justify-center rounded-[1.6rem] bg-cyan-400/10 text-xl font-black text-cyan-200 ring-1 ring-cyan-300/30">
              {initials}
              <div className="absolute -bottom-1 -right-1 flex h-7 w-7 items-center justify-center rounded-xl bg-cyan-400 text-slate-950 ring-4 ring-slate-950">
                <Camera size={14} />
              </div>
            </div>

            <div className="min-w-0">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-cyan-300">
                Missio hesabı
              </p>
              <h2 className="mt-1 truncate text-2xl font-black tracking-tight">
                {user.full_name}
              </h2>
              <div className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-black text-cyan-100">
                <BadgeCheck size={14} />
                {getRoleLabel(user.role)}
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-3 p-4">
          <InfoRow
            icon={<UserRound size={20} />}
            label="Kullanıcı adı"
            value={user.username}
          />

          <InfoRow icon={<Mail size={20} />} label="E-posta" value={emailValue} />

          <InfoRow
            icon={<Building2 size={20} />}
            label="İşletme ID"
            value={user.business_id === null ? "İşletme yok" : String(user.business_id)}
          />

          <InfoRow
            icon={<ShieldCheck size={20} />}
            label="Hesap durumu"
            value={user.is_active ? "Aktif" : "Pasif"}
          />
        </div>
      </div>

      {canShowUserManagement(user) && <UserManagementPanel currentUser={user} />}

      <div className="rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-xl shadow-slate-900/5">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
            <LockKeyhole size={22} />
          </div>

          <div>
            <h3 className="text-lg font-black tracking-tight">Güvenlik</h3>
            <p className="mt-1 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
              Mevcut şifreni doğrulayarak hesabının şifresini güvenli şekilde değiştirebilirsin.
            </p>
          </div>
        </div>

        {passwordStatusMessage && (
          <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
            {passwordStatusMessage}
          </div>
        )}

        {passwordErrorMessage && (
          <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
            {passwordErrorMessage}
          </div>
        )}

        <div className="mt-4 grid gap-3">
          <input
            value={passwordForm.current_password}
            onChange={(event) =>
              setPasswordForm((currentForm) => ({
                ...currentForm,
                current_password: event.target.value,
              }))
            }
            placeholder="Mevcut şifre"
            type="password"
            autoComplete="current-password"
            className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3 text-sm font-bold outline-none focus:border-cyan-400"
          />

          <input
            value={passwordForm.new_password}
            onChange={(event) =>
              setPasswordForm((currentForm) => ({
                ...currentForm,
                new_password: event.target.value,
              }))
            }
            placeholder="Yeni şifre"
            type="password"
            autoComplete="new-password"
            className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3 text-sm font-bold outline-none focus:border-cyan-400"
          />

          <input
            value={passwordForm.new_password_repeat}
            onChange={(event) =>
              setPasswordForm((currentForm) => ({
                ...currentForm,
                new_password_repeat: event.target.value,
              }))
            }
            placeholder="Yeni şifre tekrar"
            type="password"
            autoComplete="new-password"
            className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3 text-sm font-bold outline-none focus:border-cyan-400"
          />

          <button
            type="button"
            onClick={() => void handleChangeOwnPassword()}
            disabled={isChangingPassword}
            className="flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 text-sm font-black text-white shadow-lg shadow-teal-500/20 transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <KeyRound size={18} />
            {isChangingPassword ? "Şifre değiştiriliyor..." : "Şifremi değiştir"}
          </button>

          <div className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3">
            <div className="flex items-start gap-2">
              <Clock3 size={17} className="mt-0.5 shrink-0 text-[var(--missio-text-muted)]" />
              <p className="text-xs font-semibold leading-5 text-[var(--missio-text-muted)]">
                Şifre değişikliği bu cihazdaki mevcut oturumu kapatmaz. Diğer cihazlardaki oturumları kapatma seçeneği ileride eklenecek.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-xl shadow-slate-900/5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
              <Smartphone size={22} />
            </div>

            <div className="min-w-0">
              <h3 className="text-lg font-black tracking-tight">Push bildirimleri</h3>
              <p className="mt-1 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
                Kritik görev ve operasyon uyarılarını Firebase olmadan standart Web Push ile al.
              </p>
            </div>
          </div>

          <span
            className={
              isPushEnabled
                ? "shrink-0 rounded-full bg-emerald-50 px-3 py-1 text-xs font-black text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200"
                : "shrink-0 rounded-full bg-slate-100 px-3 py-1 text-xs font-black text-slate-600 dark:bg-slate-900 dark:text-slate-300"
            }
          >
            {isPushEnabled ? "Açık" : "Kapalı"}
          </span>
        </div>

        {pushStatusMessage && (
          <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
            {pushStatusMessage}
          </div>
        )}

        {pushErrorMessage && (
          <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
            {pushErrorMessage}
          </div>
        )}

        <button
          type="button"
          role="switch"
          aria-checked={isPushEnabled}
          onClick={() => void handleTogglePushNotifications()}
          disabled={isRequestingPushPermission}
          className="mt-4 flex min-h-14 w-full items-center justify-between gap-4 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 text-sm font-black text-[var(--missio-text-main)] transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <span>
            {isRequestingPushPermission
              ? "Bildirimler hazırlanıyor..."
              : isPushEnabled
                ? "Web Push bildirimlerini kapat"
                : "Web Push bildirimlerini aç"}
          </span>

          <span
            className={
              isPushEnabled
                ? "relative h-7 w-12 rounded-full bg-[var(--missio-primary)] shadow-inner"
                : "relative h-7 w-12 rounded-full bg-slate-300 shadow-inner dark:bg-slate-700"
            }
          >
            <span
              className={
                isPushEnabled
                  ? "absolute right-1 top-1 h-5 w-5 rounded-full bg-white shadow transition-all"
                  : "absolute left-1 top-1 h-5 w-5 rounded-full bg-white shadow transition-all"
              }
            />
          </span>
        </button>

        <button
          type="button"
          onClick={() => void handleSendWebPushTest()}
          disabled={!isPushEnabled || isSendingPushTest}
          className="mt-3 flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 text-sm font-black text-white shadow-lg shadow-teal-500/20 transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSendingPushTest ? "Test bildirimi gönderiliyor..." : "Test bildirimi gönder"}
        </button>
      </div>

      <div className="rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-xl shadow-slate-900/5">
        <h3 className="text-lg font-black tracking-tight">Hızlı ayarlar</h3>
        <p className="mt-1 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
          Tema ve oturum işlemlerini buradan yönetebilirsin.
        </p>

        <div className="mt-4 grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={onToggleTheme}
            className="flex items-center justify-center gap-2 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-4 text-sm font-black text-[var(--missio-text-main)] transition active:scale-95"
          >
            {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
            Tema değiştir
          </button>

          <button
            type="button"
            onClick={onLogout}
            className="flex items-center justify-center gap-2 rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm font-black text-red-600 transition active:scale-95 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
          >
            <LogOut size={18} />
            Çıkış yap
          </button>
        </div>
      </div>

      <div className="rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-xl shadow-slate-900/5">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
            <Smartphone size={22} />
          </div>

          <div>
            <h3 className="text-lg font-black tracking-tight">Mobil öncelikli kullanım</h3>
            <p className="mt-1 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
              Missio; görev, fotoğraf kanıtı, konum ve gün sonu kontrolünü sahada hızlı kullanmak için tasarlanıyor.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}