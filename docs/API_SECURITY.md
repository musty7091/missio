# Missio API Security

Bu doküman Missio API yüzeyinin güvenlik sınıflandırmasını tutar.

---

## 1. Public Endpoint Listesi

Aşağıdaki endpointler token olmadan çalışabilir:

| Method | Endpoint | Amaç |
|---|---|---|
| GET | `/` | Basit uygulama çalışma kontrolü |
| GET | `/api/v1/health` | Basit servis sağlık kontrolü |
| POST | `/api/v1/auth/login` | Kullanıcı girişi |

Public endpointler hassas veri döndürmemelidir.

---

## 2. Protected Endpoint Listesi

Aşağıdaki endpointler token ister:

| Method | Endpoint | Yetki |
|---|---|---|
| GET | `/api/v1/auth/me` | Giriş yapmış kullanıcı |
| GET | `/api/v1/db/health` | Sadece `super_admin` |

---

## 3. API Güvenlik Kuralları

- Public olmayan endpointler token istemelidir.
- Protected endpointlerde rol kontrolü yapılmalıdır.
- Business scope gerektiren endpointlerde `business_id` kontrolü yapılmalıdır.
- `password_hash`, secret veya gereksiz hassas veri response içinde dönmemelidir.
- Hata cevaplarında stack trace veya teknik detay dönmemelidir.
- API response'larında güvenlik headerları bulunmalıdır.
- API response'ları için `Cache-Control: no-store` kullanılmalıdır.
- Production ortamda `/docs`, `/redoc` ve `/openapi.json` kapatılmalıdır.
- API rate limit aktif olmalıdır.

---

## 4. Rate Limit

Missio ilk sürümde uygulama içi basit rate limit kullanır.

Varsayılan ayarlar:

```text
MISSIO_RATE_LIMIT_ENABLED=true
MISSIO_RATE_LIMIT_MAX_REQUESTS=120
MISSIO_RATE_LIMIT_WINDOW_SECONDS=60
```

Notlar:

- Rate limit client IP ve path bazlı uygulanır.
- `/` ve `/api/v1/health` rate limit dışındadır.
- Limit aşılırsa HTTP 429 döner.
- Response içinde `Retry-After` headerı bulunur.
- Bu yapı tek process müşteri bazlı kurulum için yeterlidir.
- İleride merkezi SaaS yapısına geçilirse Redis tabanlı distributed rate limit değerlendirilmelidir.

---

## 5. Mevcut API Güvenlik Testleri

Test dosyaları:

```text
backend/tests/test_api_security.py
backend/tests/test_rate_limit.py
```

Kontrol komutu:

```powershell
python -m app.commands.check_api_security
python -m app.commands.check_rate_limit_security
python -m pytest tests/test_api_security.py tests/test_rate_limit.py
```
