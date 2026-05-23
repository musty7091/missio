# Missio Cloud Development Workflow

## Ana Karar

Cloud'a geçmek uygulama geliştirmeyi bitirmek anlamına gelmez.

Missio geliştirilmeye local bilgisayarda devam edecek.
Google Cloud ve Firebase ilk aşamada internet üzerinde çalışan test/staging ortamı olarak kullanılacak.

## Ortamlar

### Local Development

Local geliştirme ortamı geliştiricinin bilgisayarıdır.

Backend local komutu:

cd C:\missio\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Frontend local komutu:

cd C:\missio\frontend
npm run dev -- --host 0.0.0.0 --port 5175

Local frontend adresi:

http://localhost:5175

Telefon local test adresi:

http://192.168.1.97:5175/

### Cloud Test / Staging

Cloud ortamı ilk aşamada gerçek müşteri ortamı değildir.
Bu ortam internet üzerinde çalışan test ortamıdır.

Cloud ortamında hedef yapı:

- Backend: Google Cloud Run
- Frontend: Firebase Hosting
- Database: Google Cloud SQL PostgreSQL
- Bildirim / etkileşim: Firebase servisleri

## Branch Kararı

main branch korunacaktır.

Cloud geçiş çalışmaları cloud-migration branch üzerinde yapılacaktır.

Yeni özellik geliştirmelerinde önerilen akış:

1. Localde geliştirme yapılır.
2. Backend compile testi çalıştırılır.
3. Frontend build testi çalıştırılır.
4. PostgreSQL etkisi varsa local PostgreSQL testi yapılır.
5. Git commit yapılır.
6. Cloud test ortamına deploy edilir.
7. Canlı test adresinden kontrol edilir.

## Deploy Öncesi Standart Kontroller

Backend kontrol:

cd C:\missio\backend
.\.venv\Scripts\Activate.ps1
python -m compileall app

Frontend kontrol:

cd C:\missio\frontend
npm run build

Git kontrol:

cd C:\missio
git status

Beklenen git sonucu:

nothing to commit, working tree clean

## Veritabanı Kararı

Şu an uygulamadaki veriler test amaçlıdır.
Bu nedenle ilk cloud geçişinde SQLite verileri taşınmayacaktır.

Cloud ortamında temiz PostgreSQL veritabanı kurulacaktır.
Tablolar Alembic migration ile oluşturulacaktır.
Demo kullanıcıları seed komutlarıyla yeniden oluşturulacaktır.

Demo kullanıcı standardı:

admin   | super_admin | business_id=None
patron  | boss        | business_id=1
manager | manager     | business_id=1
ahmet   | staff       | business_id=1
ali     | staff       | business_id=1

## Gerçek Kullanıcı Başladıktan Sonra Kural

Gerçek müşteri veya gerçek işletme verisi başladıktan sonra veritabanı silinmeyecektir.

Bu aşamadan sonra:

- Her şema değişikliği migration ile yapılacak.
- Deploy öncesi yedek alınacak.
- Production veritabanında doğrudan deneme yapılmayacak.
- Seed komutları dikkatli kullanılacak.
- Test verisi ile gerçek veri ayrılacak.

## Firebase Kararı

Firebase ana veritabanı olmayacaktır.

Firebase şu işler için kullanılacaktır:

- Frontend hosting
- Yeni görev bildirimi
- Görev onay/red bildirimi
- Gün kapandı bildirimi
- İleride push notification

Gerçek görev, kullanıcı, işletme, rapor ve PDF verisi backend veritabanında kalacaktır.

## Özellik Geliştirme Kuralı

Yeni özellikler önce localde geliştirilecektir.

Örnek özellikler:

- Canlı bildirim
- Personel performans ekranı
- Gelişmiş patron paneli
- Çoklu işletme yapısı
- Abonelik sistemi
- Paket ve lisans sistemi
- Fotoğraflı görev kanıtı
- Gün sonu rapor iyileştirmeleri
- PDF tasarım cilaları

Her özellik cloud'a gönderilmeden önce local testten geçecektir.

## Hata Durumunda Geri Dönüş

Cloud ortamında hata çıkarsa:

1. Local çalışan sistem korunur.
2. Problemli deploy geri alınır.
3. Veritabanı değişikliği varsa yedek kontrol edilir.
4. Hata localde yeniden üretilir.
5. Düzeltme localde test edilir.
6. Yeni commit ile tekrar deploy yapılır.

## Sıradaki Teknik Aşama

CLOUD ADIM 9:
Backend production güvenlik kontrolü.

Kontrol edilecek başlıklar:

- DEBUG=false zorunluluğu
- SECRET_KEY varsayılan değer kontrolü
- CORS ayarları
- Cloud Run health endpoint
- Production environment ayrımı
- Local çalışma düzeninin bozulmaması
