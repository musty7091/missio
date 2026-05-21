import {
  AlertCircle,
  Building2,
  Camera,
  ClipboardCheck,
  Eye,
  EyeOff,
  Loader2,
  LockKeyhole,
  LogIn,
  MapPin,
  Moon,
  ShieldCheck,
  Sun,
  User,
} from "lucide-react"
import type { FormEvent, ReactNode } from "react"
import { useState } from "react"
import { getCurrentUser, loginUser } from "../../services/authService"
import { setAccessToken } from "../../services/authTokenStorage"
import { ApiError } from "../../services/httpClient"
import type { UserMeResponse } from "../../types/auth"
import type { ThemeMode } from "../../types/task"

const IS_DEVELOPMENT_MODE = import.meta.env.DEV
const DEVELOPMENT_BUSINESS_SLUG = "missio-demo-market"
const DEVELOPMENT_USERNAME = "ahmet"

type LoginScreenProps = {
  theme: ThemeMode
  onToggleTheme: () => void
  onLoginSuccess: (user: UserMeResponse) => void
}

type LoginInputProps = {
  label: string
  value: string
  placeholder: string
  autoComplete: string
  icon: ReactNode
  type?: string
  autoCapitalize?: string
  spellCheck?: boolean
  rightElement?: ReactNode
  onChange: (value: string) => void
}

function LoginInput({
  label,
  value,
  placeholder,
  autoComplete,
  icon,
  type = "text",
  autoCapitalize,
  spellCheck,
  rightElement,
  onChange,
}: LoginInputProps) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-black text-[var(--missio-text-main)]">
        {label}
      </span>

      <div className="flex items-center gap-3 rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3 shadow-inner shadow-slate-900/[0.02] transition focus-within:border-[var(--missio-primary)] focus-within:ring-4 focus-within:ring-cyan-500/10">
        <div className="text-[var(--missio-text-muted)]">{icon}</div>

        <input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="min-w-0 flex-1 bg-transparent text-sm font-semibold text-[var(--missio-text-main)] outline-none placeholder:text-[var(--missio-text-muted)]"
          placeholder={placeholder}
          autoComplete={autoComplete}
          autoCapitalize={autoCapitalize}
          spellCheck={spellCheck}
          type={type}
        />

        {rightElement}
      </div>
    </label>
  )
}

function MissioLogoMark() {
  return (
    <div className="relative flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-300/30 bg-cyan-400/10 shadow-xl shadow-cyan-500/10">
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyan-300/30 via-blue-500/10 to-transparent" />
      <div className="relative h-7 w-8">
        <div className="absolute left-0 top-1 h-6 w-2 rounded-sm bg-cyan-300" />
        <div className="absolute left-2 top-0 h-7 w-2 rotate-[-38deg] rounded-sm bg-cyan-400" />
        <div className="absolute right-2 top-0 h-7 w-2 rotate-[38deg] rounded-sm bg-blue-500" />
        <div className="absolute right-0 top-1 h-6 w-2 rounded-sm bg-blue-600" />
        <div className="absolute right-[-3px] top-[-6px] h-2.5 w-2.5 rounded-full bg-cyan-300" />
      </div>
    </div>
  )
}

function getReadableLoginErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    if (error.status === 0) {
      return "Sunucuya bağlanılamadı. Lütfen internet bağlantını ve uygulama adresini kontrol et."
    }

    if (error.status === 401) {
      return "İşletme kodu, kullanıcı adı veya şifre hatalı."
    }

    if (error.status === 403) {
      return error.message || "Bu hesapla giriş yapılamıyor."
    }

    if (error.status === 429) {
      return "Çok fazla giriş denemesi yapıldı. Lütfen biraz bekleyip tekrar dene."
    }

    if (error.status >= 500) {
      return "Sunucu tarafında geçici bir sorun oluştu. Lütfen tekrar dene."
    }

    return error.message || "Giriş işlemi başarısız oldu."
  }

  if (error instanceof Error) {
    return error.message
  }

  return "Giriş işlemi başarısız oldu."
}

export function LoginScreen({ theme, onToggleTheme, onLoginSuccess }: LoginScreenProps) {
  const [businessSlug, setBusinessSlug] = useState(() =>
    IS_DEVELOPMENT_MODE ? DEVELOPMENT_BUSINESS_SLUG : "",
  )
  const [username, setUsername] = useState(() =>
    IS_DEVELOPMENT_MODE ? DEVELOPMENT_USERNAME : "",
  )
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  function clearErrorMessage() {
    if (errorMessage) {
      setErrorMessage(null)
    }
  }

  function handleBusinessSlugChange(value: string) {
    clearErrorMessage()
    setBusinessSlug(value)
  }

  function handleUsernameChange(value: string) {
    clearErrorMessage()
    setUsername(value)
  }

  function handlePasswordChange(value: string) {
    clearErrorMessage()
    setPassword(value)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const cleanBusinessSlug = businessSlug.trim().toLowerCase()
    const cleanUsername = username.trim()

    if (!cleanBusinessSlug) {
      setErrorMessage("İşletme kodu gerekli.")
      return
    }

    if (!cleanUsername) {
      setErrorMessage("Kullanıcı adı gerekli.")
      return
    }

    if (!password) {
      setErrorMessage("Şifre gerekli.")
      return
    }

    setErrorMessage(null)
    setIsSubmitting(true)

    try {
      const tokenResponse = await loginUser({
        business_slug: cleanBusinessSlug,
        username: cleanUsername,
        password,
      })

      setAccessToken(tokenResponse.access_token)

      const currentUser = await getCurrentUser()
      onLoginSuccess(currentUser)
    } catch (error) {
      setErrorMessage(getReadableLoginErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="min-h-screen overflow-hidden bg-[var(--missio-page-bg)] text-[var(--missio-text-main)] transition-colors duration-300">
      <section className="relative mx-auto flex min-h-screen w-full max-w-md flex-col px-4 py-4">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-56 bg-gradient-to-b from-cyan-500/20 via-blue-500/10 to-transparent blur-3xl dark:from-cyan-400/20" />
        <div className="pointer-events-none absolute -right-24 top-16 h-44 w-44 rounded-full bg-cyan-400/20 blur-3xl" />

        <header className="relative z-10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <MissioLogoMark />

            <div>
              <p className="text-2xl font-black leading-none tracking-tight text-[var(--missio-text-main)]">
                Missio
              </p>
              <p className="mt-1 text-sm font-bold tracking-wide text-cyan-500">
                Mission is possible.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onToggleTheme}
            className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm transition active:scale-95"
            aria-label="Tema değiştir"
          >
            {theme === "light" ? <Moon size={20} /> : <Sun size={20} />}
          </button>
        </header>

        <section className="relative z-10 mt-4 overflow-hidden rounded-[1.8rem] border border-cyan-300/20 bg-slate-950 p-4 text-white shadow-xl shadow-cyan-950/20">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(34,211,238,0.24),transparent_32%),linear-gradient(135deg,rgba(15,23,42,1),rgba(2,6,23,1))]" />
          <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full border border-cyan-300/20" />
          <div className="absolute right-7 top-16 h-3 w-3 rounded-full bg-cyan-300 shadow-lg shadow-cyan-300/50" />

          <div className="relative">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-[0.7rem] font-black text-cyan-200">
              <ShieldCheck size={13} />
              Mobil operasyon kontrolü
            </div>

            <h1 className="whitespace-nowrap text-xl font-black leading-tight tracking-tight min-[380px]:text-[1.35rem]">
              Görev ver. <span className="text-cyan-300">Takip et.</span> Kanıt iste.
            </h1>

            <p className="mt-3 text-sm font-medium leading-5 text-slate-300">
              Görev, fotoğraflı kanıt, konum ve gün sonu kontrolü tek ekranda.
            </p>

            <div className="mt-4 grid grid-cols-3 gap-2">
              <div className="rounded-2xl border border-white/10 bg-white/10 p-2.5 backdrop-blur">
                <ClipboardCheck className="mb-1.5 text-cyan-300" size={18} />
                <p className="text-[0.68rem] font-black leading-4">Görev Takibi</p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/10 p-2.5 backdrop-blur">
                <Camera className="mb-1.5 text-cyan-300" size={18} />
                <p className="text-[0.68rem] font-black leading-4">Fotoğraflı Kanıt</p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/10 p-2.5 backdrop-blur">
                <MapPin className="mb-1.5 text-cyan-300" size={18} />
                <p className="text-[0.68rem] font-black leading-4">Konum Kaydı</p>
              </div>
            </div>
          </div>
        </section>

        <form
          onSubmit={handleSubmit}
          className="relative z-10 mt-4 rounded-[1.8rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-xl shadow-slate-900/5"
        >
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-black tracking-tight">Giriş yap</h2>
              <p className="mt-1 text-sm font-medium leading-5 text-[var(--missio-text-muted)]">
                İşletme hesabınla Missio paneline bağlan.
              </p>
            </div>

            <div className="rounded-2xl bg-[var(--missio-primary-soft)] p-3 text-cyan-700 dark:text-cyan-200">
              <ShieldCheck size={22} />
            </div>
          </div>

          <div className="space-y-3.5">
            <LoginInput
              label="İşletme kodu"
              value={businessSlug}
              onChange={handleBusinessSlugChange}
              placeholder="missio-demo-market"
              autoComplete="organization"
              autoCapitalize="none"
              spellCheck={false}
              icon={<Building2 size={19} />}
            />

            <LoginInput
              label="Kullanıcı adı"
              value={username}
              onChange={handleUsernameChange}
              placeholder="ahmet"
              autoComplete="username"
              autoCapitalize="none"
              spellCheck={false}
              icon={<User size={19} />}
            />

            <LoginInput
              label="Şifre"
              value={password}
              onChange={handlePasswordChange}
              placeholder="Şifreni gir"
              autoComplete="current-password"
              autoCapitalize="none"
              spellCheck={false}
              type={showPassword ? "text" : "password"}
              icon={<LockKeyhole size={19} />}
              rightElement={
                <button
                  type="button"
                  onClick={() => setShowPassword((currentValue) => !currentValue)}
                  className="rounded-xl p-1 text-[var(--missio-text-muted)] transition hover:text-[var(--missio-text-main)]"
                  aria-label={showPassword ? "Şifreyi gizle" : "Şifreyi göster"}
                >
                  {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
                </button>
              }
            />
          </div>

          {errorMessage && (
            <div className="mt-4 flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold leading-5 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
              <AlertCircle className="mt-0.5 shrink-0" size={18} />
              <p>{errorMessage}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 py-4 text-sm font-black text-white shadow-lg shadow-teal-500/20 transition active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="animate-spin" size={19} />
                Giriş yapılıyor...
              </>
            ) : (
              <>
                <LogIn size={19} />
                Missio’ya giriş yap
              </>
            )}
          </button>
        </form>
      </section>
    </main>
  )
}
