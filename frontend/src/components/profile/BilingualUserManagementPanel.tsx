import {
  ChevronDown,
  ChevronUp,
  KeyRound,
  Pencil,
  Power,
  PowerOff,
  RefreshCw,
  RotateCcw,
  Save,
  Search,
  SlidersHorizontal,
  UserPlus,
  UsersRound,
  X,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { useTranslation, type AppLanguage } from "../../i18n/language"
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
import type { UserMeResponse } from "../../types/auth"

type BilingualUserManagementPanelProps = {
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

type UserManagementTexts = {
  title: string
  description: string
  statUsers: string
  statActive: string
  statPassive: string
  openManagement: string
  closeManagement: string
  refresh: string
  searchAndFilter: string
  searchPlaceholder: string
  allRoles: string
  allStatuses: string
  createUser: string
  closeCreateForm: string
  fullNamePlaceholder: string
  usernamePlaceholder: string
  emailPlaceholder: string
  temporaryPasswordPlaceholder: string
  saveUser: string
  userList: string
  showing: string
  loadingUsers: string
  noUsers: string
  edit: string
  deactivate: string
  activate: string
  roleLocked: string
  editUser: string
  accountActiveQuestion: string
  saveChanges: string
  resetPasswordTitle: string
  newTemporaryPassword: string
  resetPasswordButton: string
  roleBoss: string
  roleSuperAdmin: string
  roleManager: string
  roleStaff: string
  statusActive: string
  statusPassive: string
  loadError: string
  createError: string
  updateError: string
  statusError: string
  resetError: string
  roleError: string
  cannotDeactivateSelf: string
  createSuccess: string
  updateSuccess: string
  statusSuccess: string
  resetSuccess: string
  roleSuccess: string
}

const textsByLanguage: Record<AppLanguage, UserManagementTexts> = {
  tr: {
    title: "Kullan?c? Y?netimi",
    description: "Kullan?c? olu?turma, d?zenleme, aktif-pasif ve ?ifre s?f?rlama i?lemleri.",
    statUsers: "kullan?c?",
    statActive: "aktif",
    statPassive: "pasif",
    openManagement: "Y?netimi a?",
    closeManagement: "Y?netimi kapat",
    refresh: "Yenile",
    searchAndFilter: "Arama ve filtre",
    searchPlaceholder: "Ad, kullan?c? ad? veya e-posta ara",
    allRoles: "T?m roller",
    allStatuses: "T?m durumlar",
    createUser: "Yeni kullan?c? olu?tur",
    closeCreateForm: "Yeni kullan?c? formunu kapat",
    fullNamePlaceholder: "Ad soyad",
    usernamePlaceholder: "Kullan?c? ad?",
    emailPlaceholder: "E-posta",
    temporaryPasswordPlaceholder: "Ge?ici ?ifre",
    saveUser: "Kullan?c?y? kaydet",
    userList: "Kullan?c? listesi",
    showing: "g?steriliyor",
    loadingUsers: "Kullan?c?lar y?kleniyor...",
    noUsers: "Bu filtreye uygun kullan?c? bulunamad?.",
    edit: "D?zenle",
    deactivate: "Pasife al",
    activate: "Aktif yap",
    roleLocked: "Rol kilitli",
    editUser: "Kullan?c? d?zenle",
    accountActiveQuestion: "Hesap aktif mi?",
    saveChanges: "De?i?iklikleri kaydet",
    resetPasswordTitle: "?ifre s?f?rla",
    newTemporaryPassword: "Yeni ge?ici ?ifre",
    resetPasswordButton: "?ifreyi s?f?rla",
    roleBoss: "??letme Sahibi",
    roleSuperAdmin: "S?per Admin",
    roleManager: "Y?netici",
    roleStaff: "Personel",
    statusActive: "Aktif",
    statusPassive: "Pasif",
    loadError: "Kullan?c? listesi al?namad?.",
    createError: "Kullan?c? olu?turulamad?.",
    updateError: "Kullan?c? g?ncellenemedi.",
    statusError: "Kullan?c? durumu de?i?tirilemedi.",
    resetError: "?ifre s?f?rlanamad?.",
    roleError: "Rol de?i?tirilemedi.",
    cannotDeactivateSelf: "Kendi kullan?c?n?z? pasif hale getiremezsiniz.",
    createSuccess: "Kullan?c? olu?turuldu.",
    updateSuccess: "Kullan?c? g?ncellendi.",
    statusSuccess: "Kullan?c? durumu g?ncellendi.",
    resetSuccess: "?ifre s?f?rland?.",
    roleSuccess: "Rol g?ncellendi.",
  },
  en: {
    title: "User Management",
    description: "Create users, edit users, manage active/passive status and reset passwords.",
    statUsers: "users",
    statActive: "active",
    statPassive: "passive",
    openManagement: "Open management",
    closeManagement: "Close management",
    refresh: "Refresh",
    searchAndFilter: "Search and filter",
    searchPlaceholder: "Search by name, username or email",
    allRoles: "All roles",
    allStatuses: "All statuses",
    createUser: "Create new user",
    closeCreateForm: "Close new user form",
    fullNamePlaceholder: "Full name",
    usernamePlaceholder: "Username",
    emailPlaceholder: "Email",
    temporaryPasswordPlaceholder: "Temporary password",
    saveUser: "Save user",
    userList: "User list",
    showing: "showing",
    loadingUsers: "Users are loading...",
    noUsers: "No user was found for this filter.",
    edit: "Edit",
    deactivate: "Deactivate",
    activate: "Activate",
    roleLocked: "Role locked",
    editUser: "Edit user",
    accountActiveQuestion: "Is the account active?",
    saveChanges: "Save changes",
    resetPasswordTitle: "Reset password",
    newTemporaryPassword: "New temporary password",
    resetPasswordButton: "Reset password",
    roleBoss: "Owner",
    roleSuperAdmin: "Super Admin",
    roleManager: "Manager",
    roleStaff: "Staff",
    statusActive: "Active",
    statusPassive: "Passive",
    loadError: "User list could not be loaded.",
    createError: "User could not be created.",
    updateError: "User could not be updated.",
    statusError: "User status could not be changed.",
    resetError: "Password could not be reset.",
    roleError: "Role could not be changed.",
    cannotDeactivateSelf: "You cannot deactivate your own account.",
    createSuccess: "User created.",
    updateSuccess: "User updated.",
    statusSuccess: "User status updated.",
    resetSuccess: "Password reset.",
    roleSuccess: "Role updated.",
  },
}

const emptyCreateForm: CreateUserFormState = {
  full_name: "",
  username: "",
  password: "",
  role: "staff",
  email: "",
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

function getRoleLabel(role: string, texts: UserManagementTexts) {
  if (role === "boss") return texts.roleBoss
  if (role === "super_admin") return texts.roleSuperAdmin
  if (role === "manager") return texts.roleManager
  if (role === "staff") return texts.roleStaff
  return role
}

function getActiveLabel(isActive: boolean, texts: UserManagementTexts) {
  return isActive ? texts.statusActive : texts.statusPassive
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

function normalizeOptionalEmail(value: string) {
  const normalizedValue = value.trim().toLowerCase()
  return normalizedValue ? normalizedValue : null
}

export function BilingualUserManagementPanel({
  currentUser,
}: BilingualUserManagementPanelProps) {
  const { language } = useTranslation()
  const texts = textsByLanguage[language]

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

    return {
      totalCount: users.length,
      activeCount,
      passiveCount,
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
    } catch {
      setErrorMessage(texts.loadError)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadUsers()
  }, [currentUser.business_id, language])

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
      await createBusinessUser(currentUser.business_id, {
        full_name: createForm.full_name.trim(),
        username: createForm.username.trim().toLowerCase(),
        password: createForm.password.trim(),
        role: createForm.role,
        email: normalizeOptionalEmail(createForm.email),
        theme_preference: null,
      })

      setMessage(texts.createSuccess)
      setCreateForm(emptyCreateForm)
      setIsCreateFormOpen(false)
      await loadUsers()
    } catch {
      setErrorMessage(texts.createError)
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

      setMessage(texts.updateSuccess)
      setUsers((currentUsers) =>
        currentUsers.map((user) => (user.id === response.user.id ? response.user : user)),
      )
    } catch {
      setErrorMessage(texts.updateError)
    } finally {
      setIsSaving(false)
    }
  }

  async function handleToggleActiveStatus(targetUser: BusinessUser) {
    if (currentUser.business_id === null) {
      return
    }

    if (targetUser.id === currentUser.id) {
      setErrorMessage(texts.cannotDeactivateSelf)
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

      setMessage(texts.statusSuccess)
      setUsers((currentUsers) =>
        currentUsers.map((user) => (user.id === response.user.id ? response.user : user)),
      )
    } catch {
      setErrorMessage(texts.statusError)
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
      await resetBusinessUserPassword(currentUser.business_id, selectedUser.id, {
        new_password: resetPasswordValue.trim(),
      })

      setMessage(texts.resetSuccess)
      setResetPasswordValue("")
    } catch {
      setErrorMessage(texts.resetError)
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

      setMessage(texts.roleSuccess)
      setUsers((currentUsers) =>
        currentUsers.map((user) => (user.id === response.user.id ? response.user : user)),
      )
    } catch {
      setErrorMessage(texts.roleError)
    } finally {
      setIsSaving(false)
    }
  }

  if (currentUser.business_id === null) {
    return null
  }

  return (
    <div className="rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-xl shadow-slate-900/5">
      <div className="flex items-start gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
          <UsersRound size={22} />
        </div>

        <div className="min-w-0 flex-1">
          <h3 className="text-lg font-black tracking-tight">{texts.title}</h3>
          <p className="mt-1 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
            {texts.description}
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            <span className="rounded-full bg-[var(--missio-primary-soft)] px-3 py-1 text-xs font-black text-cyan-700 dark:text-cyan-200">
              {userStats.totalCount} {texts.statUsers}
            </span>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-black text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200">
              {userStats.activeCount} {texts.statActive}
            </span>
            <span className="rounded-full bg-red-50 px-3 py-1 text-xs font-black text-red-700 dark:bg-red-950 dark:text-red-200">
              {userStats.passiveCount} {texts.statPassive}
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
          {isManagementOpen ? texts.closeManagement : texts.openManagement}
        </button>

        <button
          type="button"
          onClick={() => void loadUsers()}
          disabled={isLoading || isSaving}
          className="flex items-center justify-center gap-2 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3 text-sm font-black text-[var(--missio-text-main)] transition active:scale-95 disabled:opacity-50"
        >
          <RefreshCw size={18} />
          {texts.refresh}
        </button>
      </div>

      {isManagementOpen && (
        <div className="mt-5 space-y-4">
          <div className="rounded-3xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-4">
            <div className="flex items-center gap-2">
              <SlidersHorizontal size={18} />
              <h4 className="text-base font-black">{texts.searchAndFilter}</h4>
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
                  placeholder={texts.searchPlaceholder}
                  className="w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] py-3 pl-11 pr-4 text-sm font-bold outline-none focus:border-cyan-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <select
                  value={roleFilter}
                  onChange={(event) => setRoleFilter(event.target.value as UserRoleFilter)}
                  className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3 text-sm font-black outline-none focus:border-cyan-400"
                >
                  <option value="all">{texts.allRoles}</option>
                  <option value="boss">{texts.roleBoss}</option>
                  <option value="manager">{texts.roleManager}</option>
                  <option value="staff">{texts.roleStaff}</option>
                </select>

                <select
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value as UserStatusFilter)}
                  className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3 text-sm font-black outline-none focus:border-cyan-400"
                >
                  <option value="all">{texts.allStatuses}</option>
                  <option value="active">{texts.statusActive}</option>
                  <option value="passive">{texts.statusPassive}</option>
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
              {isCreateFormOpen ? texts.closeCreateForm : texts.createUser}
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
                  placeholder={texts.fullNamePlaceholder}
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
                  placeholder={texts.usernamePlaceholder}
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
                  placeholder={texts.emailPlaceholder}
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
                  placeholder={texts.temporaryPasswordPlaceholder}
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
                      {getRoleLabel(role, texts)}
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
                  {texts.saveUser}
                </button>
              </div>
            )}
          </div>

          <div className="rounded-3xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-4">
            <div className="flex items-center justify-between gap-3">
              <h4 className="text-base font-black">{texts.userList}</h4>
              <span className="rounded-full bg-[var(--missio-primary-soft)] px-3 py-1 text-xs font-black text-cyan-700 dark:text-cyan-200">
                {filteredUsers.length} {texts.showing}
              </span>
            </div>

            <div className="mt-3 max-h-[28rem] space-y-2 overflow-y-auto pr-1">
              {isLoading && (
                <div className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-4 text-sm font-bold text-[var(--missio-text-muted)]">
                  {texts.loadingUsers}
                </div>
              )}

              {!isLoading && filteredUsers.length === 0 && (
                <div className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-4 text-sm font-bold text-[var(--missio-text-muted)]">
                  {texts.noUsers}
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
                              {getActiveLabel(businessUser.is_active, texts)}
                            </span>
                          </div>

                          <p className="mt-1 truncate text-xs font-bold text-[var(--missio-text-muted)]">
                            @{businessUser.username} ? {getRoleLabel(businessUser.role, texts)}
                          </p>
                        </div>

                        <button
                          type="button"
                          onClick={() => handleOpenUserForEdit(businessUser)}
                          disabled={!canEdit}
                          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] text-[var(--missio-text-main)] transition active:scale-95 disabled:opacity-40"
                          title={texts.edit}
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
                          {businessUser.is_active ? texts.deactivate : texts.activate}
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
                            <option value="manager">{texts.roleManager}</option>
                            <option value="staff">{texts.roleStaff}</option>
                          </select>
                        ) : (
                          <div className="flex items-center justify-center rounded-xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-3 py-2 text-xs font-black text-[var(--missio-text-muted)]">
                            {texts.roleLocked}
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
                    <h4 className="text-base font-black">{texts.editUser}</h4>
                  </div>

                  <p className="mt-1 text-xs font-bold text-[var(--missio-text-muted)]">
                    {selectedUser.username} ? {getRoleLabel(selectedUser.role, texts)}
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
                  placeholder={texts.fullNamePlaceholder}
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
                  placeholder={texts.emailPlaceholder}
                  className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3 text-sm font-bold outline-none focus:border-cyan-400"
                />

                <label className="flex items-center justify-between gap-3 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] px-4 py-3">
                  <span className="text-sm font-black">{texts.accountActiveQuestion}</span>
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
                  {texts.saveChanges}
                </button>
              </div>

              <div className="mt-5 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4">
                <div className="flex items-center gap-2">
                  <RotateCcw size={17} />
                  <h5 className="text-sm font-black">{texts.resetPasswordTitle}</h5>
                </div>

                <div className="mt-3 grid gap-3">
                  <input
                    value={resetPasswordValue}
                    onChange={(event) => setResetPasswordValue(event.target.value)}
                    placeholder={texts.newTemporaryPassword}
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
                    {texts.resetPasswordButton}
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
