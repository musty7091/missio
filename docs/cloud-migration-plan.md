# Missio Cloud Migration Plan

## Amaç

Missio uygulamasını mevcut özellikleri kaybetmeden Google Cloud ve Firebase altyapısına kademeli olarak taşımak.

Bu geçişte temel prensip şudur:

- Mevcut FastAPI backend korunacak.
- Mevcut React + Vite + PWA frontend korunacak.
- Mevcut rol, görev, onay, gün kapatma, rapor ve PDF mantığı korunacak.
- Firebase ana veritabanı olarak kullanılmayacak.
- Firebase ilk aşamada hosting, bildirim ve canlı etkileşim katmanı olarak değerlendirilecek.
- Ana iş verisi SQL tabanlı veritabanında kalacak.

## Mevcut Mimari

### Frontend

- React
- Vite
- PWA
- Mobil öncelikli arayüz
- Personel / Manager / Patron rol bazlı ekranlar

### Backend

- FastAPI
- SQLAlchemy
- JWT authentication
- Role based access control
- Gün sonu kapanış snapshot sistemi
- Dinamik PDF üretimi

### Local Veritabanı

- SQLite

### Kritik Ürün Özellikleri

- Personel görev akışı
- Manager operasyon yönetimi
- Patron özet ekranı
- Patron rapor arşivi
- Görev atama
- Onay / red / düzeltme akışı
- Gün kapatma
- Sorunlu gün kapatma
- 60 günlük rapor saklama kuralı
- PDF rapor indirme

## Hedef Mimari

### Frontend

React + Vite + PWA uygulaması Firebase Hosting üzerinde yayınlanacak.

Hedef:

- HTTPS destekli yayın
- PWA desteğinin korunması
- Mobil cihazlarda erişilebilirlik
- Cloud Run backend API bağlantısı

### Backend

FastAPI backend Google Cloud Run üzerinde çalışacak.

Hedef:

- Container tabanlı yayın
- Ortam değişkenleriyle güvenli yapılandırma
- Cloud SQL PostgreSQL bağlantısı
- API endpointlerinin korunması

### Veritabanı

Cloud ortamında PostgreSQL kullanılacak.

Hedef:

- SQLite sadece local geliştirme için kalacak
- Production verisi PostgreSQL üzerinde tutulacak
- Görev, kullanıcı, işletme, rapor ve PDF snapshot verileri SQL tarafında kalacak

### Firebase

Firebase aşağıdaki amaçlarla kullanılacak:

- Frontend hosting
- İleride yeni görev bildirimi
- İleride görev onay/red bildirimi
- İleride gün kapandı bildirimi
- İleride Firebase Cloud Messaging ile push notification

Firebase aşağıdaki amaçlarla kullanılmayacak:

- Ana görev veritabanı
- Gün sonu rapor veritabanı
- Kullanıcı/rol yetkilendirme ana kaynağı
- PDF rapor verisi
- İşletme ana kayıtları

## Veri Kaynağı Kararı

Missio için tek gerçek iş verisi kaynağı backend veritabanı olacaktır.

Doğru akış:

1. Manager görev atar.
2. FastAPI görevi PostgreSQL veritabanına kaydeder.
3. Backend isterse Firebase'e küçük bir bildirim sinyali gönderir.
4. Personel frontend uygulaması sinyali görür.
5. Görev listesini yine FastAPI API üzerinden yeniler.

Yanlış akış:

1. Görevi doğrudan Firebase'e yazmak.
2. FastAPI veritabanını devre dışı bırakmak.
3. Rapor snapshot mantığını Firebase üzerinden yeniden kurmak.

Bu yanlış akış kullanılmayacaktır.

## Geçiş Fazları

### Faz 0 — Emniyet

Amaç:

Mevcut çalışan sistemi garantiye almak.

Yapılacaklar:

- GitHub ana branch temiz olacak.
- Cloud çalışmaları ayrı branch üzerinde yapılacak.
- Local SQLite veritabanı yedeklenecek.
- Backend compile testi çalışacak.
- Frontend build testi çalışacak.

Durum:

Tamamlandı.

### Faz 1 — Production Config Hazırlığı

Amaç:

Backend ve frontend local ile cloud ortamını ayırabilecek hale getirilecek.

Yapılacaklar:

- Backend environment ayarları gözden geçirilecek.
- SECRET_KEY, DATABASE_URL, CORS gibi ayarlar production uyumlu hale getirilecek.
- Local SQLite desteği korunacak.
- Cloud PostgreSQL için DATABASE_URL desteği netleştirilecek.
- Frontend API base URL ayarı cloud uyumlu hale getirilecek.

### Faz 2 — PostgreSQL Hazırlığı

Amaç:

Cloud ortamında SQLite yerine PostgreSQL kullanılacak.

Yapılacaklar:

- SQLAlchemy modelleri PostgreSQL uyumluluğu açısından kontrol edilecek.
- SQLite'a özel riskli noktalar belirlenecek.
- Local test için gerekirse Docker PostgreSQL kullanılacak.
- Migration veya tablo oluşturma stratejisi netleştirilecek.

### Faz 3 — Backend Cloud Run Hazırlığı

Amaç:

FastAPI backend Cloud Run'a deploy edilebilir hale getirilecek.

Yapılacaklar:

- Dockerfile hazırlanacak.
- Cloud Run başlatma komutu netleştirilecek.
- Port ayarı Cloud Run uyumlu yapılacak.
- Health endpoint test edilecek.
- requirements.txt kontrol edilecek.

### Faz 4 — Cloud SQL Bağlantısı

Amaç:

Backend'in Cloud SQL PostgreSQL veritabanına güvenli bağlanması.

Yapılacaklar:

- Google Cloud SQL PostgreSQL instance oluşturulacak.
- Production DATABASE_URL Secret Manager veya Cloud Run environment variable üzerinden tanımlanacak.
- Backend Cloud Run ile Cloud SQL arasında bağlantı kurulacak.
- İlk tablo oluşturma / migration süreci test edilecek.

### Faz 5 — Frontend Firebase Hosting

Amaç:

React + Vite frontend Firebase Hosting üzerinde yayınlanacak.

Yapılacaklar:

- Firebase projesi oluşturulacak.
- Firebase CLI kurulacak.
- firebase.json yapılandırılacak.
- Vite build çıktısı Firebase Hosting'e deploy edilecek.
- Frontend cloud API URL ile çalışacak.

### Faz 6 — Firebase Etkileşim Katmanı

Amaç:

Manager görev atınca personel ekranı manuel yenileme olmadan haberdar olacak.

İlk sürüm:

- Akıllı otomatik yenileme
- Yeni görev algılama
- Uygulama içi uyarı
- Bildirim rozeti
- Destekleyen cihazlarda titreşim
- Tarayıcı izin verirse kısa ses

Sonraki sürüm:

- Firebase event sinyali
- Firebase Cloud Messaging
- Telefon kilitliyken push notification

## Riskler

### Risk 1 — Özellik kaybı

Önlem:

Mevcut FastAPI servisleri ve SQL modeli korunacak.

### Risk 2 — Firebase'e fazla veri taşıma

Önlem:

Firebase ana veri kaynağı yapılmayacak.

### Risk 3 — Production ayarlarının local geliştirmeyi bozması

Önlem:

Local ve production environment ayarları ayrılacak.

### Risk 4 — Veritabanı geçişinde veri kaybı

Önlem:

Her veritabanı işleminden önce yedek alınacak.

### Risk 5 — Bildirim sistemini erken karmaşıklaştırmak

Önlem:

Önce polling + uygulama içi uyarı yapılacak, sonra Firebase event veya FCM değerlendirilecek.

## Geri Dönüş Planı

Bir fazda sorun çıkarsa:

1. İlgili branch üzerinde değişiklik durdurulur.
2. Main branch korunur.
3. Local çalışan sistem kullanılmaya devam eder.
4. Problemli adım geri alınır.
5. Küçük parçalara bölünerek yeniden denenir.

## Test Listesi

Her cloud fazından sonra aşağıdaki kontroller yapılacak:

### Backend

- python -m compileall app
- Health endpoint
- Login endpoint
- Görev listeleme
- Görev atama
- Görev tamamlama
- Onay / red akışı
- Gün kapatma
- Rapor listeleme
- PDF indirme

### Frontend

- npm run build
- Patron girişi
- Manager girişi
- Personel girişi
- Mobil görünüm
- Modal açma/kapatma
- Görev atama
- Görev görüntüleme
- Rapor görüntüleme
- PDF indirme

## İlk Teknik Adım

CLOUD ADIM 2:

Backend ve frontend yapılandırma dosyaları incelenecek.

Kontrol edilecek başlıklar:

- Backend DATABASE_URL
- Backend SECRET_KEY
- Backend CORS
- Backend production debug ayarı
- Backend port ayarı
- Frontend API_BASE_URL
- Frontend build environment değişkenleri
- requirements.txt
- package.json
