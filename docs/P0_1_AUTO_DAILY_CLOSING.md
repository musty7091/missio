# Missio P0.1 - Tercihe Bağlı Otomatik Gün Kapanışı

## Karar

- Otomatik gün kapanışı işletme sahibinin tercihine bağlıdır.
- Varsayılan değer kapalıdır.
- İşletme sahibi Profil > Gün Kapanışı Ayarları bölümünden açıp kapatır.
- Açık olan işletmelerde sistem, işletmenin kendi saat dilimine göre belirlenen saatte günü otomatik kapatır.
- Varsayılan kapanış saati 23:45, varsayılan saat dilimi Asia/Nicosia olarak tasarlanmıştır.
- Tamamlanmayan görevler ertesi güne otomatik devretmez.
- Tamamlanan, onay bekleyen, reddedilen ve yapılmayan görevler günlük kapanış raporunda görünür.

## Güvenlik

Otomatik kapanış endpoint'i normal kullanıcıya açık değildir.

Endpoint:

```text
POST /api/v1/daily-closures/system/auto-close-all
```

Zorunlu header:

```text
X-Missio-System-Job-Secret: <MISSIO_SYSTEM_JOB_SECRET>
```

Backend ortam değişkeni:

```text
MISSIO_SYSTEM_JOB_SECRET=<uzun-rastgele-gizli-değer>
```

## Zamanlama

Cloud Scheduler her gün 23:45 Asia/Nicosia saatinde backend endpoint'ini çağırmalıdır.

Önemli: Scheduler sadece sistemi uyandırır. Hangi işletmenin kapanacağına backend karar verir.

Backend her işletme için şunları kontrol eder:

1. İşletme aktif mi?
2. Otomatik gün kapanışı açık mı?
3. İşletmenin kendi saat dilimine göre kapanış saati geldi mi?
4. Aynı işletme ve aynı tarih için kapanış raporu zaten var mı?

Aynı işletme + aynı tarih için ikinci kapanış raporu oluşturulmaz.

## Cloud Scheduler örnek komutu

```powershell
gcloud scheduler jobs create http missio-auto-daily-closing `
  --location europe-west1 `
  --schedule "45 23 * * *" `
  --time-zone "Asia/Nicosia" `
  --uri "https://missio-api-278096126804.europe-west1.run.app/api/v1/daily-closures/system/auto-close-all" `
  --http-method POST `
  --headers "X-Missio-System-Job-Secret=BURAYA_GIZLI_DEGER" `
  --project project-ac8ae551-ccf3-4c85-b0f
```

Mevcut job güncellemek için:

```powershell
gcloud scheduler jobs update http missio-auto-daily-closing `
  --location europe-west1 `
  --schedule "45 23 * * *" `
  --time-zone "Asia/Nicosia" `
  --uri "https://missio-api-278096126804.europe-west1.run.app/api/v1/daily-closures/system/auto-close-all" `
  --http-method POST `
  --headers "X-Missio-System-Job-Secret=BURAYA_GIZLI_DEGER" `
  --project project-ac8ae551-ccf3-4c85-b0f
```

## Deploy öncesi not

Canlı backend deploy edilmeden önce Cloud Run ortam değişkenine şu değer eklenmelidir:

```powershell
gcloud run services update missio-api `
  --region europe-west1 `
  --project project-ac8ae551-ccf3-4c85-b0f `
  --update-env-vars MISSIO_SYSTEM_JOB_SECRET=BURAYA_UZUN_RASTGELE_DEGER
```
