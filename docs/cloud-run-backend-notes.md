# Missio Backend Cloud Run Notes

Bu dosya FastAPI backend'in Google Cloud Run'a hazırlanması için oluşturuldu.

Backend Cloud Run üzerinde container olarak çalışacaktır.

Çalıştırma komutu:

python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT

Cloud Run PORT değerini environment variable olarak verir.

Production ortamında verilmesi gereken ana değerler:

MISSIO_ENVIRONMENT=production
MISSIO_DEBUG=false
MISSIO_DEFAULT_TIMEZONE=Europe/Istanbul
MISSIO_DATABASE_URL=Cloud SQL PostgreSQL bağlantısı
MISSIO_SECRET_KEY=Güçlü production secret
MISSIO_ACCESS_TOKEN_EXPIRE_MINUTES=60

Bu adımda henüz Google Cloud'a deploy yapılmaz.
Önce Docker build ve local container testi yapılır.
