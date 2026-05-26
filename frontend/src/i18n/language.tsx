import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"

export type AppLanguage = "tr" | "en"

const LANGUAGE_STORAGE_KEY = "missio-language"

const translations = {
  tr: {
    "language.selector": "Dil seçimi",
    "language.turkish": "Türkçe",
    "language.english": "English",

    "theme.toggle": "Tema değiştir",

    "role.boss": "İşletme Sahibi",
    "role.super_admin": "Süper Admin",
    "role.manager": "Yönetici",
    "role.staff": "Personel",

    "header.greeting": "Merhaba",
    "header.logout": "Çıkış yap",

    "navigation.ariaLabel": "Alt navigasyon",
    "navigation.business": "İşletme",
    "navigation.report": "Rapor",
    "navigation.system": "Sistem",
    "navigation.profile": "Profil",
    "navigation.task": "Görev",
    "navigation.notification": "Bildirim",
    "navigation.review": "Denetim",
    "navigation.summary": "Özet",
    "navigation.approval": "Onay",
    "navigation.operation": "Operasyon",
    "navigation.dayClosing": "Gün Kapanışı",

    "login.heroBadge": "Mobil operasyon kontrolü",
    "login.heroTitleStart": "Görev ver.",
    "login.heroTitleMiddle": "Takip et.",
    "login.heroTitleEnd": "Kanıt iste.",
    "login.heroDescription": "Görev, fotoğraflı kanıt, konum ve gün sonu kontrolü tek ekranda.",
    "login.featureTaskTracking": "Görev Takibi",
    "login.featurePhotoProof": "Fotoğraflı Kanıt",
    "login.featureLocationRecord": "Konum Kaydı",

    "login.title": "Giriş yap",
    "login.description": "İşletme hesabınla Missio paneline bağlan.",
    "login.businessCode": "İşletme kodu",
    "login.businessCodePlaceholder": "işletme-kodu",
    "login.username": "Kullanıcı adı",
    "login.usernamePlaceholder": "ahmet",
    "login.password": "Şifre",
    "login.passwordPlaceholder": "Şifreni gir",
    "login.showPassword": "Şifreyi göster",
    "login.hidePassword": "Şifreyi gizle",
    "login.submit": "Missio’ya giriş yap",
    "login.submitting": "Giriş yapılıyor...",

    "login.error.serverUnavailable": "Sunucuya bağlanılamadı. Lütfen internet bağlantını ve uygulama adresini kontrol et.",
    "login.error.invalidCredentials": "İşletme kodu, kullanıcı adı veya şifre hatalı.",
    "login.error.forbidden": "Bu hesapla giriş yapılamıyor.",
    "login.error.tooManyAttempts": "Çok fazla giriş denemesi yapıldı. Lütfen biraz bekleyip tekrar dene.",
    "login.error.serverError": "Sunucu tarafında geçici bir sorun oluştu. Lütfen tekrar dene.",
    "login.error.failed": "Giriş işlemi başarısız oldu.",
    "login.error.usernameRequired": "Kullanıcı adı gerekli.",
    "login.error.passwordRequired": "Şifre gerekli.",

    "task.status.assigned": "Bekliyor",
    "task.status.inProgress": "Devam ediyor",
    "task.status.completed": "Onay bekliyor",
    "task.status.completedNoApproval": "Tamamlandı",
    "task.status.approved": "Onaylandı",
    "task.status.rejected": "Reddedildi",
    "task.status.cancelled": "İptal edildi",

    "task.action.start": "Başlat",
    "task.action.complete": "Tamamla",
    "task.action.detail": "Detay",
    "task.action.resubmit": "Tekrar Gönder",
    "task.action.open": "Aç",

    "task.priority.urgent": "Acil",
    "task.priority.high": "Yüksek",
    "task.priority.normal": "Normal",
    "task.priority.low": "Düşük",

    "task.type.routine": "Rutin",
    "task.type.oneTime": "Tek seferlik",
    "task.type.routineGroupTitle": "Rutin görevler",
    "task.type.oneTimeGroupTitle": "Tek seferlik görevler",
    "task.type.routineGroupDescription": "Her gün takip edilen standart işler",
    "task.type.oneTimeGroupDescription": "Bugüne özel verilen işler",

    "task.filter.all": "Tümü",
    "task.filter.waiting": "Yapılacak",
    "task.filter.active": "Devam",
    "task.filter.completed": "Biten",

    "task.summary.todayOperation": "Bugünkü operasyon",
    "task.summary.task": "görev",
    "task.summary.completedRate": "tamamlandı",
    "task.summary.remainingTask": "Kalan görev",
    "task.summary.completed": "Biten",
    "task.summary.active": "Devam",
    "task.summary.waiting": "Yapılacak",
    "task.summary.rejected": "Red",
    "task.summary.rejectedWarning": "Reddedilen görevler tamamlanmış sayılmaz. Personel göreve tekrar girip düzeltme sonrası yeniden göndermelidir.",
    "task.summary.detailHint": "Görev detayına dokunarak işlem yapabilirsin.",

    "task.card.mustResubmit": "Tekrar gönderilmeli",
    "task.card.photo": "Fotoğraf",
    "task.card.voiceNote": "Sesli not",
    "task.card.location": "Konum",
    "task.card.approval": "Onay",
    "task.card.today": "Bugün",
  },
  en: {
    "language.selector": "Language",
    "language.turkish": "Türkçe",
    "language.english": "English",

    "theme.toggle": "Change theme",

    "role.boss": "Owner",
    "role.super_admin": "Super Admin",
    "role.manager": "Manager",
    "role.staff": "Staff",

    "header.greeting": "Hello",
    "header.logout": "Log out",

    "navigation.ariaLabel": "Bottom navigation",
    "navigation.business": "Business",
    "navigation.report": "Report",
    "navigation.system": "System",
    "navigation.profile": "Profile",
    "navigation.task": "Task",
    "navigation.notification": "Alerts",
    "navigation.review": "Review",
    "navigation.summary": "Summary",
    "navigation.approval": "Approval",
    "navigation.operation": "Operations",
    "navigation.dayClosing": "Day Closing",

    "login.heroBadge": "Mobile operation control",
    "login.heroTitleStart": "Assign tasks.",
    "login.heroTitleMiddle": "Track.",
    "login.heroTitleEnd": "Request proof.",
    "login.heroDescription": "Tasks, photo proof, location records and day-end control in one screen.",
    "login.featureTaskTracking": "Task Tracking",
    "login.featurePhotoProof": "Photo Proof",
    "login.featureLocationRecord": "Location Record",

    "login.title": "Log in",
    "login.description": "Connect to your Missio panel with your business account.",
    "login.businessCode": "Business code",
    "login.businessCodePlaceholder": "business-code",
    "login.username": "Username",
    "login.usernamePlaceholder": "john",
    "login.password": "Password",
    "login.passwordPlaceholder": "Enter your password",
    "login.showPassword": "Show password",
    "login.hidePassword": "Hide password",
    "login.submit": "Log in to Missio",
    "login.submitting": "Logging in...",

    "login.error.serverUnavailable": "Could not connect to the server. Please check your internet connection and application address.",
    "login.error.invalidCredentials": "Business code, username or password is incorrect.",
    "login.error.forbidden": "This account cannot log in.",
    "login.error.tooManyAttempts": "Too many login attempts. Please wait a moment and try again.",
    "login.error.serverError": "A temporary server error occurred. Please try again.",
    "login.error.failed": "Login failed.",
    "login.error.usernameRequired": "Username is required.",
    "login.error.passwordRequired": "Password is required.",

    "task.status.assigned": "Waiting",
    "task.status.inProgress": "In progress",
    "task.status.completed": "Waiting approval",
    "task.status.completedNoApproval": "Completed",
    "task.status.approved": "Approved",
    "task.status.rejected": "Rejected",
    "task.status.cancelled": "Cancelled",

    "task.action.start": "Start",
    "task.action.complete": "Complete",
    "task.action.detail": "Details",
    "task.action.resubmit": "Resubmit",
    "task.action.open": "Open",

    "task.priority.urgent": "Urgent",
    "task.priority.high": "High",
    "task.priority.normal": "Normal",
    "task.priority.low": "Low",

    "task.type.routine": "Routine",
    "task.type.oneTime": "One-time",
    "task.type.routineGroupTitle": "Routine tasks",
    "task.type.oneTimeGroupTitle": "One-time tasks",
    "task.type.routineGroupDescription": "Standard tasks tracked every day",
    "task.type.oneTimeGroupDescription": "Tasks assigned specifically for today",

    "task.filter.all": "All",
    "task.filter.waiting": "To do",
    "task.filter.active": "Active",
    "task.filter.completed": "Done",

    "task.summary.todayOperation": "Today's operation",
    "task.summary.task": "tasks",
    "task.summary.completedRate": "completed",
    "task.summary.remainingTask": "Remaining tasks",
    "task.summary.completed": "Done",
    "task.summary.active": "Active",
    "task.summary.waiting": "To do",
    "task.summary.rejected": "Rejected",
    "task.summary.rejectedWarning": "Rejected tasks are not counted as completed. The staff member must reopen the task, correct it and submit it again.",
    "task.summary.detailHint": "Tap a task detail to take action.",

    "task.card.mustResubmit": "Must be resubmitted",
    "task.card.photo": "Photo",
    "task.card.voiceNote": "Voice note",
    "task.card.location": "Location",
    "task.card.approval": "Approval",
    "task.card.today": "Today",
  },
} as const

export type TranslationKey = keyof typeof translations.tr

type LanguageContextValue = {
  language: AppLanguage
  setLanguage: (language: AppLanguage) => void
  t: (key: TranslationKey) => string
}

const LanguageContext = createContext<LanguageContextValue | null>(null)

function isAppLanguage(value: string | null): value is AppLanguage {
  return value === "tr" || value === "en"
}

function getInitialLanguage(): AppLanguage {
  const savedLanguage = window.localStorage.getItem(LANGUAGE_STORAGE_KEY)

  if (isAppLanguage(savedLanguage)) {
    return savedLanguage
  }

  return "tr"
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<AppLanguage>(getInitialLanguage)

  useEffect(() => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language)
    document.documentElement.lang = language
    document.documentElement.dir = "ltr"
  }, [language])

  const value = useMemo<LanguageContextValue>(() => {
    return {
      language,
      setLanguage,
      t: (key) => translations[language][key] ?? translations.tr[key] ?? key,
    }
  }, [language])

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useTranslation() {
  const context = useContext(LanguageContext)

  if (!context) {
    throw new Error("useTranslation must be used inside LanguageProvider.")
  }

  return context
}
