import { LogIn, Moon, ShieldCheck, Sparkles, Sun } from "lucide-react"
import type { FormEvent } from "react"
import { useState } from "react"
import { loginUser, getCurrentUser } from "../../services/authService"
import { setAccessToken } from "../../services/authTokenStorage"
import type { UserMeResponse } from "../../types/auth"
import type { ThemeMode } from "../../types/task"

type LoginScreenProps = {
  theme: ThemeMode
  onToggleTheme: () => void
  onLoginSuccess: (user: UserMeResponse) => void
}

export function LoginScreen({ theme, onToggleTheme, onLoginSuccess }: LoginScreenProps) {
  const [businessSlug, setBusinessSlug] = useState("missio-demo-market")
  const [username, setUsername] = useState("ahmet")
  const [password, setPassword] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage(null)
    setIsSubmitting(true)

    try {
      const tokenResponse = await loginUser({
        business_slug: businessSlug.trim() || null,
        username: username.trim(),
        password,
      })

      setAccessToken(tokenResponse.access_token)

      const currentUser = await getCurrentUser()
      onLoginSuccess(currentUser)
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Giriş işlemi başarısız oldu.")
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="min-h-screen bg-[var(--missio-page-bg)] px-4 py-5 text-[var(--missio-text-main)] transition-colors duration-300">
      <section className="mx-auto flex min-h-[calc(100vh-40px)] w-full max-w-md flex-col justify-between">
        <header className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-[var(--missio-text-muted)]">Missio</p>
            <h1 className="mt-1 text-2xl font-black tracking-tight">Mission is possible.</h1>
          </div>

          <button
            type="button"
            onClick={onToggleTheme}
            className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-3 shadow-sm"
            aria-label="Tema değiştir"
          >
            {theme === "light" ? <Moon size={20} /> : <Sun size={20} />}
          </button>
        </header>

        <section className="my-8 overflow-hidden rounded-[2.25rem] bg-slate-950 p-6 text-white shadow-2xl shadow-slate-900/20 dark:bg-slate-900">
          <div className="mb-8 flex items-start justify-between gap-4">
            <div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-bold text-teal-200">
                <Sparkles size={14} />
                Mobil operasyon kontrolü
              </div>

              <h2 className="text-4xl font-black tracking-tight">İşletmeni tek ekrandan yönet.</h2>

              <p className="mt-4 text-sm leading-6 text-slate-300">
                Görev, fotoğraf kanıtı, konum ve manager onayı Missio içinde birleşir.
              </p>
            </div>

            <div className="rounded-3xl bg-white/10 p-3">
              <ShieldCheck className="text-teal-300" size={32} />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-2xl bg-white/10 p-3">
              <p className="text-xl font-bold">PWA</p>
              <p className="mt-1 text-xs text-slate-300">Mobil hissi</p>
            </div>
            <div className="rounded-2xl bg-white/10 p-3">
              <p className="text-xl font-bold">Kanıt</p>
              <p className="mt-1 text-xs text-slate-300">Fotoğraf</p>
            </div>
            <div className="rounded-2xl bg-white/10 p-3">
              <p className="text-xl font-bold">Anlık</p>
              <p className="mt-1 text-xs text-slate-300">Kontrol</p>
            </div>
          </div>
        </section>

        <form
          onSubmit={handleSubmit}
          className="rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-5 shadow-xl shadow-slate-900/5"
        >
          <div className="mb-5">
            <h2 className="text-xl font-black tracking-tight">Giriş yap</h2>
            <p className="mt-1 text-sm text-[var(--missio-text-muted)]">
              İşletme hesabınla Missio paneline bağlan.
            </p>
          </div>

          <div className="space-y-4">
            <label className="block">
              <span className="mb-2 block text-sm font-bold">İşletme kodu</span>
              <input
                value={businessSlug}
                onChange={(event) => setBusinessSlug(event.target.value)}
                className="w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3 text-sm outline-none transition focus:border-[var(--missio-primary)]"
                placeholder="missio-demo-market"
                autoComplete="organization"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-bold">Kullanıcı adı</span>
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3 text-sm outline-none transition focus:border-[var(--missio-primary)]"
                placeholder="ahmet"
                autoComplete="username"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-bold">Şifre</span>
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] px-4 py-3 text-sm outline-none transition focus:border-[var(--missio-primary)]"
                placeholder="Şifreni gir"
                type="password"
                autoComplete="current-password"
              />
            </label>
          </div>

          {errorMessage && (
            <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
              {errorMessage}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl bg-[var(--missio-primary)] px-4 py-4 text-sm font-black text-white shadow-lg shadow-teal-500/20 disabled:cursor-not-allowed disabled:opacity-70"
          >
            <LogIn size={19} />
            {isSubmitting ? "Giriş yapılıyor..." : "Missio’ya giriş yap"}
          </button>
        </form>
      </section>
    </main>
  )
}
