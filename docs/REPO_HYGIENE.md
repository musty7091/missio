# Missio Repository Hygiene

Bu doküman Missio repository hijyen ve secret sızıntısı kontrollerini açıklar.

---

## Amaç

Uygulama güvenli olsa bile yanlışlıkla `.env`, SQLite veritabanı, log, upload veya geçici kurulum dosyası repoya giderse güvenlik riski oluşur.

Bu nedenle Missio'da repository hijyeni güvenlik kapısının parçasıdır.

---

## Kontrol Komutu

Backend klasörü içinde çalıştırılır:

```powershell
cd C:\missio\backend
python -m app.commands.check_repo_hygiene
```

---

## Kontrol Edilen Başlıklar

- `.env` dosyası git tarafından takip edilmemeli
- SQLite database dosyaları git tarafından takip edilmemeli
- `ADIM_*.py` ve `ADIM_*.ps1` geçici yardımcı dosyaları repoya girmemeli
- `__pycache__` ve `.pyc` dosyaları repoya girmemeli
- Upload, temp ve log klasörleri repoya girmemeli
- `.gitignore` temel koruma kurallarını içermeli
- Security gate workflow dosyası bulunmalı
- Security dokümanları bulunmalı
- `requirements.txt` içinde kaldırılmış dependency kalmamalı

---

## Security Gate Entegrasyonu

Repository hygiene kontrolü merkezi güvenlik kapısına eklenmiştir:

```powershell
python -m app.commands.check_security_gate
```

---

## Not

Bu kontrol özellikle takip edilen dosyalara odaklanır.

Yerelde duran ama git tarafından takip edilmeyen geçici dosyalar ayrıca temizlenebilir. Ancak asıl kritik konu bu dosyaların repoya girmemesidir.
