# Missio Cloud Production Config Decisions

## Ana Karar

Missio Firebase'e komple taşınmayacak.

Mevcut yapı korunacak:

- Backend: FastAPI
- Frontend: React + Vite + PWA
- Ana veritabanı: SQL tabanlı veritabanı
- Cloud veritabanı hedefi: PostgreSQL
- Frontend hosting hedefi: Firebase Hosting
- Backend hosting hedefi: Google Cloud Run

## Firebase Kullanım Kararı

Firebase ana veritabanı olmayacak.

Firebase şu işler için kullanılacak:

- Frontend hosting
- Bildirim sinyali
- İleride Firebase Cloud Messaging
- İleride push notification

Firebase şu işler için kullanılmayacak:

- Görev ana verisi
- Kullanıcı/rol ana verisi
- Gün sonu rapor verisi
- PDF rapor verisi
- İşletme ana kayıtları

## Backend Production Kararları

Production ortamında:

MISSIO_ENVIRONMENT=production
MISSIO_DEBUG=false
MISSIO_DEFAULT_TIMEZONE=Europe/Istanbul
MISSIO_DATABASE_URL=PostgreSQL bağlantısı
MISSIO_SECRET_KEY=Cloud Run ortam değişkeni veya Secret Manager
MISSIO_ACCESS_TOKEN_EXPIRE_MINUTES=60

## Frontend Production Kararları

Production ortamında:

VITE_API_BASE_URL=https://cloud-run-backend-adresi/api/v1

Local ortamda:

VITE_API_BASE_URL=http://localhost:8000/api/v1

## Cloud Run Kararı

Backend Cloud Run üzerinde çalışacak.

Cloud Run için uygulama:

0.0.0.0:\

üzerinden çalışmalıdır.

## Local Çalışma Korunacak

Aşağıdaki local komutlar bozulmayacak:

Backend:
cd C:\missio\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Frontend:
cd C:\missio\frontend
npm run dev -- --host 0.0.0.0 --port 5175

## Sıradaki Teknik İşler

1. Frontend .env dosyası oluşturulacak.
2. Backend production config kontrol edilecek.
3. Backend Dockerfile hazırlanacak.
4. Cloud Run hazırlığı yapılacak.
5. Firebase Hosting hazırlığı yapılacak.
