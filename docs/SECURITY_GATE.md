# Missio Security Gate

Bu doküman Missio güvenlik kapısı komutunu açıklar.

Güvenlik kapısı; auth, token, brute-force, audit log, rol kontrolü, business scope, API güvenliği, rate limit ve production config kontrollerini tek noktadan çalıştırır.

---

## Komut

Backend klasörü içinde çalıştırılır:

```powershell
cd C:\missio\backend
python -m app.commands.check_security_gate
```

---

## Kapsam

Bu komut şu kontrolleri çalıştırır:

- Baseline tablo kontrolü
- Production güvenlik ayar kontrolü
- Auth güvenlik temel kontrolü
- JWT token güvenlik kontrolü
- Auth service kontrolü
- Login brute-force ve audit log kontrolü
- Role ve business scope kontrolü
- Auth endpoint kontrolü
- API güvenlik kontrolü
- Rate limit kontrolü
- Güvenlik odaklı pytest seti

---

## Kullanım Zamanı

Bu komut şu durumlarda çalıştırılmalıdır:

- Yeni güvenlik değişikliğinden sonra
- Auth veya kullanıcı sistemi değiştiğinde
- Endpoint güvenlik davranışı değiştiğinde
- Migration değişikliğinden sonra
- Satışa hazırlık kontrolünden önce
- Release öncesinde

---

## Başarı Kriteri

Komut sonunda şu çıktı görülmelidir:

```text
Missio güvenlik kapısı başarılı.
```

Bu çıktı yoksa ürün güvenlik kapısından geçmiş sayılmaz.

---

## Not

Bu komut local geliştirme ortamında çalışır.

Production kuruluma geçildiğinde ayrıca gerçek ortam değişkenleri, HTTPS, dosya yetkileri, backup/restore ve müşteri teslim kontrolleri yapılmalıdır.

---

## GitHub Actions Entegrasyonu

Merkezi güvenlik kapısı GitHub Actions üzerinde de çalıştırılır.

Workflow dosyası:

```text
.github/workflows/security-gate.yml
```

Detaylı doküman:

```text
docs/CI_SECURITY_GATE.md
```

---

## Dependency Health Kontrolü

Güvenlik kapısı artık dependency health kontrolünü de çalıştırır.

Komut:

```powershell
python -m app.commands.check_dependency_health
```

Detaylı doküman:

```text
docs/DEPENDENCY_SECURITY.md
```

---

## Repository Hygiene Kontrolü

Güvenlik kapısı artık repository hijyen kontrolünü de çalıştırır.

Komut:

```powershell
python -m app.commands.check_repo_hygiene
```

Detaylı doküman:

```text
docs/REPO_HYGIENE.md
```

---

## Bootstrap Durum Kontrolü

Güvenlik kapısı artık initial super admin bootstrap durum kontrolünü de çalıştırır.

Komut:

```powershell
python -m app.commands.check_bootstrap_status
```

Detaylı doküman:

```text
docs/BOOTSTRAP.md
```

---

## Business Creation Kontrolü

Güvenlik kapısı artık super admin ile işletme oluşturma kontrolünü de çalıştırır.

Komut:

```powershell
python -m app.commands.check_business_creation
```

Detaylı doküman:

```text
docs/BUSINESS_CREATION.md
```

---

## Business User Management Kontrolü

Güvenlik kapısı artık işletme kullanıcısı oluşturma kontrolünü de çalıştırır.

Komut:

```powershell
python -m app.commands.check_business_user_management
```

Detaylı doküman:

```text
docs/BUSINESS_USER_MANAGEMENT.md
```
