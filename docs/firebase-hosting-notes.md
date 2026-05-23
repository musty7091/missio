# Missio Firebase Hosting Notes

## Amaç

Bu dosya Missio frontend uygulamasının Firebase Hosting hazırlığını açıklar.

## Hosting Kararı

Frontend React + Vite uygulaması Firebase Hosting üzerinde yayınlanacaktır.

Firebase Hosting public directory:

frontend/dist

Bu klasör frontend build işleminden sonra oluşur.

Build komutu:

cd C:\missio\frontend
npm run build

## SPA Rewrite Kararı

Missio tek sayfa React uygulamasıdır.

Bu nedenle Firebase Hosting üzerinde tüm route istekleri /index.html dosyasına yönlendirilir.

firebase.json içinde kullanılan rewrite:

source: **
destination: /index.html

## Deploy Henüz Yapılmadı

Bu adımda sadece Firebase Hosting yapılandırması yapılmıştır.

Canlı deploy sonraki adımda kontrollü yapılacaktır.

## Production API Adresi

Firebase Hosting deploy edilmeden önce frontend production API adresi Cloud Run backend adresine göre ayarlanmalıdır.

Örnek:

VITE_API_BASE_URL=https://missio-api-xxxxx.run.app/api/v1

Şu an backend Cloud Run adresi henüz oluşmadığı için Firebase deploy yapılmayacaktır.

## Sonraki Adım

CLOUD ADIM 14:
Cloud Run backend deploy hazırlığı ve Google Cloud servislerinin kontrollü açılması.
