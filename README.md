# Missio

## Mission is possible.

Missio, küçük işletmeler için görev atama, konumlu işlem kaydı, fotoğraflı kanıt ve gün sonu raporlama sistemidir.

Ana fikir:

> Görev ver. Takip et. Kanıtla. Raporla.

Missio klasik bir yapılacaklar listesi değildir. Missio; küçük işletmelerin günlük operasyonlarını, personel görevlerini, saha kontrollerini, konumlu işlem kayıtlarını ve fotoğraflı kanıt süreçlerini düzenli şekilde takip edebilmesi için tasarlanmış profesyonel bir web uygulamasıdır.

---

## 1. Proje Vizyonu

Missio’nun hedefi; küçük işletmelerin patron, yönetici ve personel arasındaki görev akışını sade, güvenilir ve kanıtlanabilir hale getirmektir.

Patron görev verir. Personel telefonundan işlemi yapar. Sistem işlem zamanını, işlem geçmişini, gerekli durumlarda konumu ve fotoğraflı kanıtı kayıt altına alır. Gün sonunda patron kimin ne yaptığını, hangi görevlerin tamamlandığını, hangi işlerin geciktiğini ve hangi görevlerin kanıtla desteklendiğini rapor olarak görür.

---

## 2. Ürün Tanımı

Missio, müşteri bazlı ayrı kurulabilen, web tabanlı, mobil öncelikli bir görev operasyon sistemidir.

İlk sürümde merkezi SaaS modeli kullanılmayacaktır. Her müşteri için ayrı kurulum, ayrı uygulama ve ayrı veritabanı mantığı uygulanacaktır.

Bu yaklaşım sayesinde:

- Her müşterinin verisi ayrı tutulur.
- Kurulum ve teslim süreci kolaylaşır.
- SQLite ile düşük maliyetli başlangıç yapılabilir.
- Küçük işletmelere hızlı şekilde satılabilir MVP çıkarılabilir.
- İleride ihtiyaç olursa PostgreSQL ve SaaS mimarisine geçiş kapısı açık bırakılır.

---

## 3. Hedef Kullanıcılar

Missio şu işletmeler için tasarlanır:

- Marketler
- Zincir veya yarı zincir küçük işletmeler
- Saha personeli bulunan işletmeler
- Depo ve raf kontrolü yapan işletmeler
- Teslimat veya müşteri ziyareti yapan ekipler
- Günlük açılış / kapanış kontrolü yapmak isteyen işletmeler
- Patronun gün sonunda net operasyon raporu görmek istediği işletmeler

---

## 4. Ana Satış Mantığı

Missio’nun satış cümlesi:

> Patron görev verir. Personel telefonundan işlemi yapar. Sistem zamanı, konumu, fotoğrafı ve tüm işlem geçmişini kayıt altına alır. Gün sonunda patron kimin ne yaptığını, hangi görevlerin geciktiğini ve hangi işlerin tamamlandığını rapor olarak görür.

---

## 5. Görsel Tasarım Kararı

Missio’nun ana tasarım dili, proje başlangıcında belirlenen tanıtım ve dashboard görsellerindeki çizgiye göre korunacaktır.

Tasarım karakteri:

- Koyu lacivert / gece mavisi premium tema
- Cyan / turkuaz vurgu rengi
- Modern SaaS kalitesi
- Mobil öncelikli yapı
- Personel tarafında telefon ekranı önceliği
- Patron / yönetici tarafında masaüstü ve mobil dashboard
- Büyük kartlar
- Net istatistikler
- Temiz ikonlar
- Harita, konum, görev, fotoğraf kanıtı ve rapor hissi
- Profesyonel, güven veren, kurumsal ama sade görünüm

Dark mode ana marka karakteridir. Light mode ayrıca desteklenecektir.

---

## 6. Temel Ürün Kararları

İlk sürüm için kararlar:

- Tek kod tabanı kullanılacaktır.
- Her müşteriye ayrı kurulum yapılacaktır.
- Her müşteri kendi veritabanı ile çalışacaktır.
- İlk aşamada merkezi SaaS, tenant ve abonelik altyapısı yapılmayacaktır.
- SQLite ilk sürüm için ana veritabanı olacaktır.
- SQLAlchemy ile PostgreSQL geçiş kapısı açık tutulacaktır.
- Paket seçimine göre modüller aktif veya pasif olacaktır.
- Kurulum sihirbazı ile müşteri işletmesine uygun yapılandırma yapılacaktır.
- İlk hedef çalışan, güvenli, profesyonel görünümlü ve satılabilir MVP olacaktır.

---

## 7. MVP Kapsamı

İlk satılabilir MVP içinde olması gerekenler:

- Giriş sistemi
- Rol bazlı kullanıcı sistemi
- Patron paneli
- Yönetici paneli
- Personel mobil paneli
- Görev oluşturma
- Görev atama
- Görev durum takibi
- Görev işlem geçmişi
- İşlem anı konum kaydı
- Fotoğraflı kanıt ekleme
- Günlük görev özeti
- Personel bazlı temel performans raporu
- Paket ve modül mantığı
- Kurulum sihirbazı temel yapısı
- SQLite veritabanı
- Migration sistemi
- Audit log sistemi
- Dark mode / light mode altyapısı

---

## 8. Kullanıcı Rolleri

### Süper Admin

Sistemin kurulum ve teknik yönetim kullanıcısıdır.

Yetkileri:

- Kurulum sihirbazını yönetir.
- Paket seçimini yapar.
- Aktif / pasif modülleri belirler.
- Lisans ve paket bilgilerini düzenler.
- İşletme bilgilerini oluşturur.
- İlk patron hesabını oluşturur.
- Sistem ayarlarını görür.
- Destek ve bakım işlemlerini yapar.

Süper Admin günlük işletme kullanıcısı değildir.

### Patron

İşletme içindeki en yüksek operasyonel yetkili kullanıcıdır.

Yetkileri:

- Tüm paneli görür.
- Personel ekler.
- Yönetici ekler.
- Görev oluşturur.
- Görev atar.
- Görev durumlarını takip eder.
- Konumlu işlem loglarını görür.
- Fotoğraflı kanıtları görür.
- Gün sonu raporlarını alır.
- Personel performansını takip eder.
- İşletme içi ayarları yönetir.

### Yönetici

Günlük operasyonu yöneten kullanıcıdır.

Yetkileri:

- Görev oluşturabilir.
- Görev atayabilir.
- Personel görevlerini takip edebilir.
- Rapor görebilir.
- Görevleri onaylayabilir veya reddedebilir.

Yönetici sistem kurulumu, lisans ve paket ayarlarını değiştiremez.

### İşletme Sahibi

Lisans sahibi, ödeme sahibi veya işletme sahibi bilgisini temsil eder.

İlk sürümde Patron ile aynı kullanıcı olabilir. Ancak veritabanında işletme sahibi veya lisans sahibi bilgisi ayrıca tutulmalıdır.

### Personel

Sadece kendisine atanan görevleri görür.

Yetkileri:

- Kendisine atanan görevleri görür.
- Göreve başladım seçebilir.
- Tamamladım seçebilir.
- Müşteriye ulaştım seçebilir.
- Yapılamadı seçebilir.
- Not ekleyebilir.
- Fotoğraf ekleyebilir.
- Kendi işlem geçmişini görebilir.

Personel başka personelin görevlerini göremez.

---

## 9. Konum Kaydı Mantığı

Missio sürekli konum takibi yapmayacaktır.

Konum sadece belirli görev işlemleri sırasında alınacaktır.

Konum alınacak ana işlemler:

- Göreve başladım
- Tamamladım
- Müşteriye ulaştım

Konum alınması isteğe bağlı veya ayara bağlı olabilecek işlemler:

- Görevi gördüm
- Not ekledim
- Fotoğraf ekledim
- Yapılamadı

Konum kaydında tutulacak bilgiler:

- Enlem
- Boylam
- Doğruluk değeri
- Tarih / saat
- Kullanıcı
- Görev
- İşlem türü
- IP bilgisi
- User agent / cihaz bilgisi
- Konum izni durumu

Personel, konumun sürekli değil sadece işlem anında alınacağını açık şekilde bilmelidir.

---

## 10. Fotoğraflı Kanıt Mantığı

Görevlerde fotoğraflı kanıt sistemi bulunacaktır.

Fotoğraf dosyaları veritabanına gömülmeyecektir. Fotoğraflar dosya sisteminde tutulacak, metadata bilgisi SQLite içinde saklanacaktır.

Örnek klasör yapısı:

storage/uploads/tasks
storage/reports
storage/backups

Fotoğraf metadata bilgileri:

- Görev bilgisi
- İşlem bilgisi
- Yükleyen kullanıcı
- Dosya yolu
- Dosya adı
- Dosya türü
- Dosya boyutu
- Yükleme tarihi
- İsteğe bağlı konum bilgisi

---

## 11. Paket Yapısı

### Başlangıç Paketi

- Patron paneli
- Personel girişi
- Görev oluşturma
- Görev atama
- Temel işlem geçmişi
- Günlük görev özeti
- 5 personele kadar kullanım

### Pro Paket

- Başlangıç paketindeki tüm özellikler
- Konumlu işlem kaydı
- Fotoğraflı görev kanıtı
- Görev şablonları
- Açılış / kapanış kontrol listeleri
- Personel bazlı performans raporu
- PDF / Excel rapor çıktısı
- 15 personele kadar kullanım

### Saha Paketi

- Pro paketindeki tüm özellikler
- Saha görevleri
- Müşteri / teslimat lokasyonu
- Harita üzerinde işlem noktaları
- Fotoğraf + konum + saat kanıtı
- Günlük saha performans raporu
- 25 personele kadar kullanım

---

## 12. Modül Mantığı

Modüller sadece arayüzde gizlenmeyecektir. Backend tarafında da kontrol edilecektir.

Her modülün benzersiz bir kodu olacaktır.

Örnek modül kodları:

- task_core
- staff_panel
- location_logs
- photo_proof
- task_templates
- daily_reports
- pdf_export
- excel_export
- field_tasks
- setup_wizard
- license_manager
- theme_manager

Pasif modüle API isteği gelirse sistem izin vermeyecektir.

---

## 13. Özellik Bayrakları

Örnek özellik bayrakları:

- enable_location_on_start
- enable_location_on_complete
- enable_location_on_customer_arrival
- enable_photo_required
- enable_manager_approval
- enable_daily_report
- enable_pdf_export
- enable_excel_export
- enable_geofence_warning
- enable_staff_limit
- max_staff_count
- default_theme
- timezone

---

## 14. SQLite Veritabanı Yaklaşımı

İlk sürümde SQLite kullanılacaktır.

SQLite kullanım kuralları:

- Foreign key desteği her bağlantıda aktif edilecektir.
- WAL modu kullanılacaktır.
- Busy timeout ayarlanacaktır.
- Migration sistemi kurulacaktır.
- Veritabanı yedekleme sistemi baştan düşünülecektir.
- Fotoğraf dosyaları veritabanına gömülmeyecektir.
- Tarih, saat, log ve rapor tutarlılığı dikkatle ele alınacaktır.
- Aynı anda çok yoğun yazma gerektiren yapıdan kaçınılacaktır.

---

## 15. Ana Veritabanı Tabloları

İlk planlanan tablolar:

- app_settings
- businesses
- users
- packages
- modules
- business_modules
- business_features
- tasks
- task_events
- task_attachments
- task_categories
- task_templates
- notifications
- daily_reports
- audit_logs
- setup_state
- licenses
- consent_documents
- user_consents

---

## 16. Görev Durumları

İlk görev durumları:

- assigned
- in_progress
- customer_reached
- completed_by_staff
- approved
- rejected
- unable_to_complete
- cancelled
- reopened

Gecikme ayrıca hesaplanacaktır.

Bir görev için due_at_utc geçmişse ve görev tamamlanmamışsa görev gecikmiş kabul edilir.

---

## 17. İşlem Log Türleri

task_events içinde tutulacak temel işlem türleri:

- task_created
- task_assigned
- task_started
- customer_reached
- task_completed
- task_unable_to_complete
- task_approved
- task_rejected
- task_reopened
- note_added
- photo_added
- due_date_changed
- priority_changed
- assignee_changed
- task_cancelled

Log sistemi Missio’nun kalbidir.

Kritik hiçbir işlem logsuz kalmamalıdır.

---

## 18. Raporlama Yaklaşımı

İlk raporlar:

### Günlük Operasyon Özeti

- Toplam görev
- Tamamlanan görev
- Devam eden görev
- Geciken görev
- Yapılamayan görev
- Onay bekleyen görev
- Başarı oranı

### Personel Performans Raporu

- Personele atanan görev sayısı
- Tamamlanan görev sayısı
- Zamanında tamamlanan görev sayısı
- Geciken görev sayısı
- Yapılamayan görev sayısı
- Ortalama tamamlama süresi
- Fotoğraf kanıtı bulunan görev sayısı
- Konum kaydı bulunan işlem sayısı

### Konumlu İşlem Raporu

- Göreve başlama konumu
- Müşteriye ulaşıldı konumu
- Tamamlama konumu
- Konum doğruluğu
- İşletme dışından tamamlanan görevler
- Düşük doğrulukla alınan konumlar

### Fotoğraflı Kanıt Raporu

- Fotoğraf isteyen görevler
- Fotoğraf eklenen görevler
- Fotoğraf eklenmeyen görevler
- Personel bazlı fotoğraf kanıtı oranı

### Geciken Görev Raporu

- Görev adı
- Atanan personel
- Son teslim zamanı
- Tamamlanma zamanı
- Gecikme süresi
- Açıklama

### Kurulum Teslim Raporu

- İşletme adı
- Paket adı
- Aktif modüller
- Personel limiti
- Timezone
- Tema tercihi
- Oluşturulan kullanıcılar
- Kurulum tarihi
- Admin kullanıcı bilgisi
- Teslim notları

---

## 19. Kurulum Sihirbazı

Kurulum sihirbazı adımları:

1. Hoş geldiniz ekranı
2. Paket seçimi
3. İşletme bilgileri
4. Timezone seçimi
5. Admin / patron hesabı oluşturma
6. Personel kullanıcıları oluşturma
7. Modül seçimi
8. Görev kategorileri
9. Hazır görev şablonları
10. Konum ayarları
11. Fotoğraf kanıt ayarları
12. Rapor ayarları
13. Tema tercihi
14. KVKK / personel bilgilendirme ayarları
15. Yedekleme ayarları
16. Lisans / paket bilgisi
17. Kurulum teslim özeti

Kurulum sonunda sistem bir kurulum teslim raporu oluşturabilmelidir.

---

## 20. Timezone Yaklaşımı

Her işletmenin timezone ayarı olacaktır.

Varsayılan değer:

Europe/Istanbul

Teknik yaklaşım:

- Veritabanında tarih / saat değerleri UTC saklanacaktır.
- Ekranda işletmenin timezone ayarına göre gösterilecektir.
- Günlük raporlar işletmenin yerel gününe göre hesaplanacaktır.
- Gün sonu raporu işletmenin yerel gününe göre oluşacaktır.

Timezone önemli olan alanlar:

- Görev oluşturma zamanı
- Son teslim zamanı
- Göreve başlama zamanı
- Tamamlama zamanı
- Müşteriye ulaşıldı zamanı
- Gecikme hesaplama
- Gün sonu raporu
- Haftalık / aylık raporlar
- Audit log kayıtları
- Kurulum tarihi
- Lisans başlangıç / bitiş tarihleri

---

## 21. Güvenlik Yaklaşımı

İlk sürümden itibaren güvenlik temel kabul edilecektir.

Kurallar:

- Şifreler açık metin saklanmayacaktır.
- Şifreler güvenli hash yöntemi ile saklanacaktır.
- JWT tabanlı kimlik doğrulama kullanılacaktır.
- Rol bazlı erişim kontrolü uygulanacaktır.
- Personel sadece kendi görevlerini görecektir.
- Kritik işlemler audit log tablosuna yazılacaktır.
- Soft delete yaklaşımı tercih edilecektir.
- Patron logları silememelidir.
- Silme işlemleri de loglanmalıdır.
- Pasif modüllere backend seviyesinde erişim engellenmelidir.

---

## 22. KVKK ve Personel Bilgilendirme Yaklaşımı

Konum verisi ve personel işlem kayıtları hassas veridir.

Bu yüzden:

- Personel ilk girişte bilgilendirme metnini görmelidir.
- Konumun ne zaman alınacağı açık şekilde yazılmalıdır.
- Sürekli konum takibi yapılmadığı belirtilmelidir.
- Sadece belirli görev işlemleri sırasında konum alınmalıdır.
- Konum izni reddedilirse bu durum loglanmalıdır.
- İşletme ayarına göre işlem engellenebilir veya uyarı gösterilebilir.
- Kullanıcı onayları kayıt altına alınmalıdır.

---

## 23. Bildirim Mantığı

İlk aşamada uygulama içi bildirim yeterlidir.

Bildirim tetikleyicileri:

- Yeni görev atandı
- Görev gecikti
- Personel göreve başladı
- Personel müşteriye ulaştı
- Personel görevi tamamladı
- Görev onay bekliyor
- Görev reddedildi
- Personel not ekledi
- Fotoğraf eklendi

İlerleyen sürümlerde değerlendirilecek bildirimler:

- E-posta bildirimi
- PWA web bildirimi
- Telegram bildirimi
- WhatsApp entegrasyonu

İlk sürümde WhatsApp entegrasyonu yapılmayacaktır.

---

## 24. Teknoloji Yığını

### Backend

- Python
- FastAPI
- SQLAlchemy 2.x
- Alembic
- SQLite
- Pydantic
- JWT tabanlı kimlik doğrulama
- Güvenli parola hash sistemi

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- PWA uyumlu yapı
- Mobil öncelikli personel ekranı
- Dashboard odaklı patron ekranı
- Dark mode / light mode desteği

### Dosya Depolama

İlk aşamada yerel dosya sistemi kullanılacaktır.

---

## 25. Backend Klasör Yapısı

Planlanan backend klasör yapısı:

backend/
    app/
        core/
        db/
        models/
        schemas/
        services/
        repositories/
        api/
            routes/
        modules/
            tasks/
            users/
            reports/
            setup/
            licensing/
            notifications/
            audit/
        utils/
    alembic/
    tests/

---

## 26. Frontend Klasör Yapısı

Planlanan frontend klasör yapısı:

frontend/
    src/
        app/
        components/
        features/
            auth/
            tasks/
            dashboard/
            staff/
            reports/
            setup/
            settings/
        lib/
        services/
        types/
        routes/

---

## 27. Kodlama Kuralları

Bu projede şu kurallar uygulanacaktır:

- Adım adım ilerlenir.
- Aynı anda çok dosya değiştirilmez.
- Her adımda yapılan işlem açık yazılır.
- Kodlar tam dosya olarak verilir.
- Patch / diff kullanılmaz.
- Kısaltılmış kod verilmez.
- “Buraya önceki kod gelecek” gibi ifadeler kullanılmaz.
- Verilen dosya doğrudan kopyalanabilir olmalıdır.
- Fonksiyon ve dosya isimleri gereksiz yere değiştirilmez.
- Gereksiz refactor yapılmaz.
- Önce çalışan temel yapı, sonra geliştirme yapılır.
- Her adımın sonunda test komutları ve beklenen sonuç yazılır.
- Hata olursa mevcut dosya üzerinden minimum düzeltme yapılır.
- Backend kodlarında profesyonel İngilizce isimlendirme tercih edilir.
- UI metinleri Türkçe olabilir.
- Satır uzunluğu mümkün olduğunca 100 karakteri geçmemelidir.
- Okunabilirlik birinci önceliktir.

---

## 28. Test Yaklaşımı

İlk aşamada test yaklaşımı:

- Backend endpoint testleri
- Veritabanı bağlantı testi
- Migration testi
- Auth testi
- Rol bazlı erişim testi
- Görev oluşturma testi
- Personel kendi görevini görme testi
- Başka personelin görevini görememe testi
- Konum log testi
- Fotoğraf metadata testi
- Günlük rapor hesaplama testi

---

## 29. Yol Haritası

Kabaca ilerleme planı:

| Aşama | Hedef | Yaklaşık İlerleme |
|---|---|---:|
| 1 | Proje tanımı ve README | %5 |
| 2 | Repo / klasör yapısı | %10 |
| 3 | Backend temel kurulum | %15 |
| 4 | SQLite bağlantısı ve migration | %22 |
| 5 | Auth / kullanıcı sistemi | %32 |
| 6 | İşletme / paket / modül sistemi | %42 |
| 7 | Görev sistemi | %55 |
| 8 | Mobil personel paneli | %65 |
| 9 | Konumlu işlem logları | %73 |
| 10 | Fotoğraflı kanıt | %80 |
| 11 | Raporlama | %88 |
| 12 | Kurulum sihirbazı | %94 |
| 13 | UI cilası, testler ve paketleme | %100 |

---

## 30. Mevcut İlerleme Durumu

Proje ilerleme durumu:

%5

Bu oran sadece proje tanımı ve ana karar dokümanı tamamlandığında geçerlidir.

---

## 31. İlk Geliştirme Adımı

README tamamlandıktan sonraki ilk geliştirme adımı:

Proje klasör yapısını oluşturmak.

Bu adımda henüz iş mantığı yazılmayacaktır.

Önce şu temel yapı hazırlanacaktır:

- backend klasörü
- frontend klasörü
- storage klasörü
- docs klasörü
- .gitignore
- backend için temel Python proje dosyaları
- frontend için Vite + React + TypeScript başlangıcı

---

## 32. Marka Notu

Missio’nun marka karakteri:

- Güvenilir
- Sade
- Profesyonel
- Mobil öncelikli
- Operasyon odaklı
- Kanıt ve rapor merkezli
- Küçük işletmeler için ulaşılabilir
- Görsel olarak premium

Slogan:

Mission is possible.
