# Missio Initial Super Admin Bootstrap

Bu doküman Missio ilk kurulum super admin oluşturma modelini açıklar.

---

## Kurulum Modeli

İlk ticari kurulum modeli:

1. Uygulama kurulumu müşteri yerinde Mustafa tarafından yapılır.
2. İlk kullanıcı `super_admin` olarak oluşturulur.
3. Bu kullanıcı işletme oluşturma, işletme sahibi hesabı açma ve teknik yönetim için kullanılır.
4. Müşterinin günlük kullanıcıları daha sonra `boss`, `manager` ve `staff` rolleriyle oluşturulur.

---

## Güvenlik Kuralları

- Gömülü sabit şifre yoktur.
- Varsayılan admin şifresi yoktur.
- İlk kurulum sadece kullanıcı yokken yapılabilir.
- İlk super admin oluşturulunca `app_settings.setup_completed = true` yapılır.
- İkinci kez bootstrap çalıştırılamaz.
- Şifre güvenlik politikasına uymak zorundadır.
- Şifre audit log'a yazılmaz.
- `setup.super_admin_created` audit log kaydı oluşturulur.

---

## Durum Kontrolü

```powershell
cd C:\missio\backend
python -m app.commands.check_bootstrap_status
```

---

## İlk Super Admin Oluşturma

Etkileşimli kullanım:

```powershell
cd C:\missio\backend
python -m app.commands.bootstrap_super_admin
```

Parametreli kullanım:

```powershell
python -m app.commands.bootstrap_super_admin --full-name "Mustafa Karadeniz" --username mustafa --email mustafa@example.com --password "GüçlüŞifre.2026!" --yes
```

Not: Parametreli kullanım terminal geçmişinde şifre bırakabilir. Gerçek kurulumda etkileşimli kullanım daha güvenlidir.

---

## Security Gate Entegrasyonu

Bootstrap durum kontrolü merkezi güvenlik kapısına eklenmiştir:

```powershell
python -m app.commands.check_security_gate
```
