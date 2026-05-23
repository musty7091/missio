# Missio Cloud Live Test Notes

## Test Tarihi

2026-05-23

## Frontend

Firebase Hosting URL:

https://missio-cloud-cyprus.web.app/

## Backend

Cloud Run API URL:

https://missio-api-2jug4yr7za-ew.a.run.app

Health endpoint:

https://missio-api-2jug4yr7za-ew.a.run.app/api/v1/health

## Database

Cloud SQL PostgreSQL

Instance ID: missio-db
Database name: missio_prod
Application user: missio_app

## Demo Kullanıcılar

admin   / Missio.2026! / super_admin
patron  / Missio.2026! / boss
manager / Missio.2026! / manager
ahmet   / Missio.2026! / staff
ali     / Missio.2026! / staff

## Yapılan Canlı Testler

- Firebase Hosting sayfası açıldı.
- Patron ekranı açıldı.
- Manager ekranı açıldı.
- Ahmet ile giriş yapıldı.
- Ali ile giriş yapıldı.
- Ahmet ve Ali için ayrı görevler göründü.
- Tarayıcı adresi doğru kaldı: https://missio-cloud-cyprus.web.app/

## Sonuç

Missio ilk cloud test sürümü başarıyla çalışır hale geldi.

## Sonraki Aşamalar

- Canlı ortamda manager görev atama testi
- Ahmet/Ali görev tamamlama testi
- Manager onay/red testi
- Gün kapatma testi
- Patron rapor arşivi testi
- PDF indirme testi
- Firebase bildirim altyapısı
- Cloud deploy tekrar edilebilir hale getirme
