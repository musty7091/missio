# Missio Security Checklist

Bu doküman Missio projesinin güvenlik kapısıdır.

Missio; görev, personel, konum, fotoğraf kanıtı, işlem geçmişi ve günlük rapor gibi hassas operasyon verileri tuttuğu için güvenlik ilk sürümden itibaren zorunlu kabul edilir.

Bu dosyadaki başlıklar tamamlanmadan Missio satılabilir MVP olarak kabul edilmeyecektir.

---

## 1. Güvenlik Prensibi

Ana kural:

> Özellik çalışıyor diye tamamlanmış sayılmaz. Güvenlik kontrolü ve testi yoksa özellik tamamlanmış değildir.

Missio geliştirme yaklaşımı:

- Önce güvenli temel.
- Sonra iş mantığı.
- Sonra arayüz.
- En son satışa hazırlık.

---

## 2. P0 Güvenlik Kapısı

Aşağıdaki maddeler tamamlanmadan görev modülü, fotoğraf kanıtı, raporlama ve frontend cilasına geçilmeyecektir.

### 2.1 Kimlik Doğrulama

- [x] Parola hash sistemi kurulacak.
- [x] Parola güç politikası uygulanacak.
- [x] JWT access token temeli kurulacak.
- [x] Kullanıcı oluşturma servisi kurulacak.
- [x] Kullanıcı doğrulama servisi kurulacak.
- [ ] Login endpoint yazılacak.
- [ ] Login attempt tablosu eklenecek.
- [ ] Başarısız giriş denemeleri loglanacak.
- [ ] Brute-force koruması eklenecek.
- [ ] Belirli sayıda hatalı giriş sonrası geçici kilit uygulanacak.
- [ ] Başarılı girişte `last_login_at` güncellenecek.
- [ ] Başarılı ve başarısız login audit log'a yazılacak.
- [ ] Pasif kullanıcı login olamayacak.
- [ ] Zayıf veya varsayılan şifre ile kullanıcı oluşturulamayacak.
- [ ] Şifre değişimi ayrıca loglanacak.

### 2.2 Yetki ve Rol Kontrolü

- [x] Rol sabitleri oluşturulacak.
- [ ] Endpoint seviyesinde rol dependency yazılacak.
- [ ] Servis seviyesinde yetki kontrolü uygulanacak.
- [ ] Repository sorgularında `business_id` filtresi zorunlu hale getirilecek.
- [ ] Personel sadece kendi görevlerini görebilecek.
- [ ] Yönetici sadece kendi işletmesinin verilerini görebilecek.
- [ ] Patron sadece kendi işletmesinin verilerini görebilecek.
- [ ] Süper Admin günlük personel işlemi yapan kullanıcı gibi tasarlanmayacak.
- [ ] Pasif modüller backend seviyesinde engellenecek.

### 2.3 Token ve Oturum Güvenliği

- [x] Access token üretimi yapılacak.
- [x] Access token doğrulama yapılacak.
- [x] Süresi dolmuş token reddedilecek.
- [x] Geçersiz rol ile token üretimi engellenecek.
- [ ] Production ortamda zayıf `SECRET_KEY` ile uygulama açılmayacak.
- [ ] Token içinde gereksiz hassas veri tutulmayacak.
- [ ] Token response içinde sadece gerekli alanlar dönecek.
- [ ] Kritik işlemlerde kullanıcı yetkisi tekrar kontrol edilecek.

### 2.4 Audit Log

- [ ] Audit log servis katmanı yazılacak.
- [ ] Login başarılı olayı loglanacak.
- [ ] Login başarısız olayı loglanacak.
- [ ] Kullanıcı oluşturma loglanacak.
- [ ] Kullanıcı pasifleştirme loglanacak.
- [ ] Rol değişikliği loglanacak.
- [ ] Görev oluşturma loglanacak.
- [ ] Görev atama loglanacak.
- [ ] Göreve başlama loglanacak.
- [ ] Müşteriye ulaşıldı işlemi loglanacak.
- [ ] Görev tamamlama loglanacak.
- [ ] Konum izni reddi loglanacak.
- [ ] Fotoğraf ekleme loglanacak.
- [ ] Rapor oluşturma loglanacak.
- [ ] Lisans veya paket değişimi loglanacak.
- [ ] Backup ve restore işlemleri loglanacak.
- [ ] Kritik loglar kullanıcı tarafından silinemeyecek.

### 2.5 API Güvenliği

- [ ] Public endpoint listesi açıkça belirlenecek.
- [ ] Public olmayan endpointlerin tamamı token isteyecek.
- [ ] Role dependency uygulanacak.
- [ ] Business scope dependency uygulanacak.
- [ ] Pydantic input validation kullanılacak.
- [ ] Hata cevaplarında teknik detay sızdırılmayacak.
- [ ] Response modellerinde `password_hash`, secret, token gibi alanlar dönmeyecek.
- [ ] Production CORS ayarları herkese açık olmayacak.
- [ ] Rate limit eklenecek.
- [ ] API testleri yazılacak.

### 2.6 Fotoğraf Yükleme Güvenliği

- [ ] Fotoğraf dosyaları veritabanına gömülmeyecek.
- [ ] Dosya yolu metadata olarak tutulacak.
- [ ] Dosya adı sistem tarafından güvenli üretilecek.
- [ ] Kullanıcının yüklediği orijinal dosya adı path olarak kullanılmayacak.
- [ ] Path traversal engellenecek.
- [ ] Sadece izin verilen uzantılar kabul edilecek.
- [ ] MIME/type kontrolü yapılacak.
- [ ] Maksimum dosya boyutu sınırı uygulanacak.
- [ ] Upload klasörü çalıştırılabilir kod alanı olmayacak.
- [ ] Fotoğraf yükleme işlemi audit log'a yazılacak.
- [ ] Fotoğraf metadata kaydı görev ve kullanıcı ile ilişkilendirilecek.

### 2.7 Konum ve KVKK

- [ ] Konum sürekli takip edilmeyecek.
- [ ] Konum sadece işlem anında alınacak.
- [ ] Konum alınacak işlemler açıkça belirlenecek.
- [ ] Konum izni reddedilirse bu durum loglanacak.
- [ ] Personel ilk girişte bilgilendirme metni görecek.
- [ ] Personel onayı kayıt altına alınacak.
- [ ] Konum kaydında enlem, boylam, doğruluk, tarih, kullanıcı, görev, IP ve user agent tutulacak.
- [ ] Konum verisi sadece yetkili kullanıcılar tarafından görülebilecek.
- [ ] Personel başka personelin konum kayıtlarını göremeyecek.

### 2.8 Veritabanı ve Migration Güvenliği

- [x] SQLite foreign key desteği aktif edilecek.
- [x] SQLite WAL modu kullanılacak.
- [x] SQLite busy timeout ayarlanacak.
- [x] Alembic migration altyapısı kurulacak.
- [x] Baseline schema oluşturulacak.
- [x] Baseline tablo kontrol komutu eklenecek.
- [ ] Migration öncesi otomatik yedekleme eklenecek.
- [ ] Backup standardı belirlenecek.
- [ ] Backup doğrulama sistemi eklenecek.
- [ ] Restore testi eklenecek.
- [ ] Canlı veride destructive migration kontrollü yapılacak.
- [ ] Soft delete yaklaşımı kritik tablolarda uygulanacak.

### 2.9 Konfigürasyon ve Secret Güvenliği

- [x] `.env` dosyası git dışında tutulacak.
- [ ] Production ortamda debug kapalı olacak.
- [ ] Production ortamda güçlü `SECRET_KEY` zorunlu olacak.
- [ ] Varsayılan admin şifresiyle teslim yapılmayacak.
- [ ] Kurulum teslim raporunda şifre açık yazılmayacak.
- [ ] Loglarda token veya şifre görünmeyecek.
- [ ] GitHub'a veritabanı, upload dosyası veya secret gitmeyecek.
- [ ] Production güvenlik kontrol komutu yazılacak.

---

## 3. Her Yeni Özellik İçin Zorunlu Sorular

Her yeni endpoint, servis veya modül için şu sorular cevaplanacaktır:

- Bu endpoint kim tarafından kullanılabilir?
- Personel başka işletmenin verisine erişebilir mi?
- Personel başka personelin verisine erişebilir mi?
- Bu işlem `business_id` filtresi gerektiriyor mu?
- Bu işlem audit log gerektiriyor mu?
- Bu işlem rate limit gerektiriyor mu?
- Bu veri hassas mı?
- Bu veri response içinde dönmeli mi?
- Bu işlem soft delete mi olmalı?
- Bu işlem için test yazıldı mı?
- Hata durumunda teknik detay sızıyor mu?
- Production ortamda bu özellik güvenli çalışır mı?

---

## 4. Güvenlik Testleri

Missio güvenlik testleri şu gruplarda ilerleyecektir:

- Auth testleri
- Token testleri
- Rol yetki testleri
- Business scope testleri
- Personel veri izolasyonu testleri
- Brute-force testleri
- Audit log testleri
- Dosya yükleme güvenliği testleri
- Konum izni ve konum log testleri
- Production config testleri

---

## 5. Güvenlik Tamamlanma Kriteri

Bir modül şu koşullar sağlanmadan tamamlanmış sayılmaz:

- Endpoint çalışıyor.
- Yetki kontrolü var.
- Business scope kontrolü var.
- Gerekli audit log var.
- Input validation var.
- Hassas veri sızdırmıyor.
- Hata cevapları güvenli.
- Testleri yazılmış.
- Testleri geçiyor.

---

## 6. Mevcut Güvenlik İlerleme Durumu

Mevcut durumda tamamlanan temel güvenlik parçaları:

- Parola hash sistemi
- Parola güç politikası
- Rol sabitleri
- JWT access token temeli
- Token doğrulama testleri
- Kullanıcı repository temeli
- Auth service temeli
- Kullanıcı oluşturma ve doğrulama testleri
- SQLite güvenli bağlantı ayarları
- Alembic migration altyapısı
- Baseline schema kontrol komutu

Sıradaki güvenlik adımı:

> ADIM 5D — Login attempt, brute-force koruması ve auth audit log.
