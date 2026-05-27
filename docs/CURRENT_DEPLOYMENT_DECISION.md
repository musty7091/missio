# Missio Güncel Yayın Kararı

Missio için güncel satış/test öncesi yayın kararı aşağıdaki gibidir.

## Aktif altyapı

- Frontend: React + Vite + PWA, Cloud Run üzerinde Nginx ile servis edilir.
- Backend: FastAPI, Cloud Run üzerinde çalışır.
- Bildirim: Firebase kullanılmadan standart Web Push / VAPID kullanılır.
- Veritabanı: PostgreSQL / Cloud SQL hedeflenir.

## Kullanılmayacak altyapı

- Firebase Hosting
- Firebase Cloud Messaging
- Firebase Admin SDK
- firebase.json deploy akışı
- firebase-messaging-sw.js servis işçisi

## Deploy öncesi kontrol

Kod değişikliklerinden sonra küçük küçük deploy yapılmaz. Önce lokal kontrol çalıştırılır:

```powershell
.\scripts\check_before_deploy.ps1
```

Bu kontrol başarılı olmadan Cloud Run deploy yapılmamalıdır.
