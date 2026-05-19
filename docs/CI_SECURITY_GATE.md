# Missio GitHub Actions Security Gate

Bu doküman Missio için GitHub Actions üzerinde çalışan otomatik güvenlik kapısını açıklar.

---

## Amaç

Yerelde çalışan güvenlik kapısı artık GitHub üzerinde de her push ve pull request işleminde otomatik çalışır.

Böylece auth, token, brute-force, audit log, role control, business scope, API security, rate limit ve production config kontrollerinden biri bozulursa GitHub bunu hemen gösterir.

---

## Workflow Dosyası

```text
.github/workflows/security-gate.yml
```

---

## Çalışma Zamanı

Workflow şu durumlarda çalışır:

- `main` branch üzerine push yapılınca
- `main` branch hedefli pull request açılınca veya güncellenince

---

## Çalıştırılan Adımlar

GitHub Actions şu sırayla çalışır:

```text
1. Repository checkout
2. Python 3.12 kurulumu
3. requirements.txt paket kurulumu
4. .env.example üzerinden CI .env oluşturma
5. Alembic migration uygulama
6. Seed referans verilerini yükleme
7. Merkezi güvenlik kapısını çalıştırma
```

Ana kontrol komutu:

```powershell
python -m app.commands.check_security_gate
```

---

## Başarı Kriteri

Workflow başarılı değilse ilgili commit güvenlik kapısından geçmiş kabul edilmez.

Beklenen yerel çıktı:

```text
Missio güvenlik kapısı başarılı.
```

---

## Not

Bu workflow local SQLite tabanlı CI doğrulaması yapar.

Production kuruluma geçildiğinde ayrıca gerçek ortam değişkenleri, HTTPS, backup/restore, dosya izinleri ve müşteri teslim kontrolleri ayrı doğrulanacaktır.
