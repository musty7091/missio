import {
  BadgeCheck,
  Building2,
  Camera,
  Clock3,
  KeyRound,
  LockKeyhole,
  LogOut,
  Mail,
  Moon,
  ShieldCheck,
  Smartphone,
  Sun,
  UserRound,
} from "lucide-react"
import type { ReactNode } from "react"
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

type ComingSoonActionCardProps = {
  icon: ReactNode
  title: string
  description: string
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

function ComingSoonActionCard({ icon, title, description }: ComingSoonActionCardProps) {
  return (
    <div className="rounded-2xl border border-[var(--missio-border)] bg-[var(--missio-page-bg)] p-4">
      <div className="flex items-start gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
          {icon}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <h4 className="text-sm font-black text-[var(--missio-text-main)]">
              {title}
            </h4>

            <span className="shrink-0 rounded-full bg-amber-50 px-2.5 py-1 text-[0.65rem] font-black text-amber-700 dark:bg-amber-950 dark:text-amber-200">
              Yakında
            </span>
          </div>

          <p className="mt-1 text-xs font-semibold leading-5 text-[var(--missio-text-muted)]">
            {description}
          </p>
        </div>
      </div>
    </div>
  )
}

export function ProfilePanel({ user, theme, onToggleTheme, onLogout }: ProfilePanelProps) {
  const emailValue = user.email && user.email.trim() ? user.email : "E-posta tanımlı değil"
  const initials = getInitials(user.full_name)

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

          <InfoRow
            icon={<Mail size={20} />}
            label="E-posta"
            value={emailValue}
          />

          <InfoRow
            icon={<Building2 size={20} />}
            label="İşletme ID"
            value={String(user.business_id)}
          />

          <InfoRow
            icon={<ShieldCheck size={20} />}
            label="Hesap durumu"
            value={user.is_active ? "Aktif" : "Pasif"}
          />
        </div>
      </div>

      <div className="rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-xl shadow-slate-900/5">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
            <LockKeyhole size={22} />
          </div>

          <div>
            <h3 className="text-lg font-black tracking-tight">Güvenlik</h3>
            <p className="mt-1 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
              Şifre değiştirme işlemi mevcut şifre doğrulamasıyla güvenli şekilde hazırlanacak.
            </p>
          </div>
        </div>

        <div className="mt-4 space-y-3">
          <ComingSoonActionCard
            icon={<KeyRound size={21} />}
            title="Şifre değiştir"
            description="Mevcut şifre, yeni şifre ve yeni şifre tekrarı ile güvenli şifre değiştirme akışı eklenecek."
          />

          <ComingSoonActionCard
            icon={<Clock3 size={21} />}
            title="Oturum güvenliği"
            description="Şifre değişince diğer cihazlardaki oturumları kapatma seçeneği ileride eklenecek."
          />
        </div>
      </div>

      <div className="rounded-[2rem] border border-[var(--missio-border)] bg-[var(--missio-card-bg)] p-4 shadow-xl shadow-slate-900/5">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--missio-primary-soft)] text-cyan-700 dark:text-cyan-200">
            <Camera size={22} />
          </div>

          <div>
            <h3 className="text-lg font-black tracking-tight">Profil görünümü</h3>
            <p className="mt-1 text-sm font-semibold leading-6 text-[var(--missio-text-muted)]">
              Personel ve manager ekranlarında kullanıcıyı daha hızlı tanımak için profil fotoğrafı desteği hazırlanacak.
            </p>
          </div>
        </div>

        <div className="mt-4">
          <ComingSoonActionCard
            icon={<Camera size={21} />}
            title="Profil fotoğrafı değiştir"
            description="Güvenli dosya kontrolü, küçük profil görseli ve varsayılan avatar desteğiyle eklenecek."
          />
        </div>
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
