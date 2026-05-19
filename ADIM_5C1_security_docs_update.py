from __future__ import annotations

from pathlib import Path
import re

ROOT_DIR = Path(r"C:\missio")
README_PATH = ROOT_DIR / "README.md"
SECURITY_PATH = ROOT_DIR / "docs" / "SECURITY_CHECKLIST.md"

SECURITY_CHECKLIST = "# Missio Security Checklist\n\nBu doküman Missio projesinin güvenlik kapısıdır.\n\nMissio; görev, personel, konum, fotoğraf kanıtı, işlem geçmişi ve günlük rapor gibi hassas operasyon verileri tuttuğu için güvenlik ilk sürümden itibaren zorunlu kabul edilir.\n\nBu dosyadaki başlıklar tamamlanmadan Missio satılabilir MVP olarak kabul edilmeyecektir.\n\n---\n\n## 1. Güvenlik Prensibi\n\nAna kural:\n\n> Özellik çalışıyor diye tamamlanmış sayılmaz. Güvenlik kontrolü ve testi yoksa özellik tamamlanmış değildir.\n\nMissio geliştirme yaklaşımı:\n\n- Önce güvenli temel.\n- Sonra iş mantığı.\n- Sonra arayüz.\n- En son satışa hazırlık.\n\n---\n\n## 2. P0 Güvenlik Kapısı\n\nAşağıdaki maddeler tamamlanmadan görev modülü, fotoğraf kanıtı, raporlama ve frontend cilasına geçilmeyecektir.\n\n### 2.1 Kimlik Doğrulama\n\n- [x] Parola hash sistemi kurulacak.\n- [x] Parola güç politikası uygulanacak.\n- [x] JWT access token temeli kurulacak.\n- [x] Kullanıcı oluşturma servisi kurulacak.\n- [x] Kullanıcı doğrulama servisi kurulacak.\n- [ ] Login endpoint yazılacak.\n- [ ] Login attempt tablosu eklenecek.\n- [ ] Başarısız giriş denemeleri loglanacak.\n- [ ] Brute-force koruması eklenecek.\n- [ ] Belirli sayıda hatalı giriş sonrası geçici kilit uygulanacak.\n- [ ] Başarılı girişte `last_login_at` güncellenecek.\n- [ ] Başarılı ve başarısız login audit log'a yazılacak.\n- [ ] Pasif kullanıcı login olamayacak.\n- [ ] Zayıf veya varsayılan şifre ile kullanıcı oluşturulamayacak.\n- [ ] Şifre değişimi ayrıca loglanacak.\n\n### 2.2 Yetki ve Rol Kontrolü\n\n- [x] Rol sabitleri oluşturulacak.\n- [ ] Endpoint seviyesinde rol dependency yazılacak.\n- [ ] Servis seviyesinde yetki kontrolü uygulanacak.\n- [ ] Repository sorgularında `business_id` filtresi zorunlu hale getirilecek.\n- [ ] Personel sadece kendi görevlerini görebilecek.\n- [ ] Yönetici sadece kendi işletmesinin verilerini görebilecek.\n- [ ] Patron sadece kendi işletmesinin verilerini görebilecek.\n- [ ] Süper Admin günlük personel işlemi yapan kullanıcı gibi tasarlanmayacak.\n- [ ] Pasif modüller backend seviyesinde engellenecek.\n\n### 2.3 Token ve Oturum Güvenliği\n\n- [x] Access token üretimi yapılacak.\n- [x] Access token doğrulama yapılacak.\n- [x] Süresi dolmuş token reddedilecek.\n- [x] Geçersiz rol ile token üretimi engellenecek.\n- [ ] Production ortamda zayıf `SECRET_KEY` ile uygulama açılmayacak.\n- [ ] Token içinde gereksiz hassas veri tutulmayacak.\n- [ ] Token response içinde sadece gerekli alanlar dönecek.\n- [ ] Kritik işlemlerde kullanıcı yetkisi tekrar kontrol edilecek.\n\n### 2.4 Audit Log\n\n- [ ] Audit log servis katmanı yazılacak.\n- [ ] Login başarılı olayı loglanacak.\n- [ ] Login başarısız olayı loglanacak.\n- [ ] Kullanıcı oluşturma loglanacak.\n- [ ] Kullanıcı pasifleştirme loglanacak.\n- [ ] Rol değişikliği loglanacak.\n- [ ] Görev oluşturma loglanacak.\n- [ ] Görev atama loglanacak.\n- [ ] Göreve başlama loglanacak.\n- [ ] Müşteriye ulaşıldı işlemi loglanacak.\n- [ ] Görev tamamlama loglanacak.\n- [ ] Konum izni reddi loglanacak.\n- [ ] Fotoğraf ekleme loglanacak.\n- [ ] Rapor oluşturma loglanacak.\n- [ ] Lisans veya paket değişimi loglanacak.\n- [ ] Backup ve restore işlemleri loglanacak.\n- [ ] Kritik loglar kullanıcı tarafından silinemeyecek.\n\n### 2.5 API Güvenliği\n\n- [ ] Public endpoint listesi açıkça belirlenecek.\n- [ ] Public olmayan endpointlerin tamamı token isteyecek.\n- [ ] Role dependency uygulanacak.\n- [ ] Business scope dependency uygulanacak.\n- [ ] Pydantic input validation kullanılacak.\n- [ ] Hata cevaplarında teknik detay sızdırılmayacak.\n- [ ] Response modellerinde `password_hash`, secret, token gibi alanlar dönmeyecek.\n- [ ] Production CORS ayarları herkese açık olmayacak.\n- [ ] Rate limit eklenecek.\n- [ ] API testleri yazılacak.\n\n### 2.6 Fotoğraf Yükleme Güvenliği\n\n- [ ] Fotoğraf dosyaları veritabanına gömülmeyecek.\n- [ ] Dosya yolu metadata olarak tutulacak.\n- [ ] Dosya adı sistem tarafından güvenli üretilecek.\n- [ ] Kullanıcının yüklediği orijinal dosya adı path olarak kullanılmayacak.\n- [ ] Path traversal engellenecek.\n- [ ] Sadece izin verilen uzantılar kabul edilecek.\n- [ ] MIME/type kontrolü yapılacak.\n- [ ] Maksimum dosya boyutu sınırı uygulanacak.\n- [ ] Upload klasörü çalıştırılabilir kod alanı olmayacak.\n- [ ] Fotoğraf yükleme işlemi audit log'a yazılacak.\n- [ ] Fotoğraf metadata kaydı görev ve kullanıcı ile ilişkilendirilecek.\n\n### 2.7 Konum ve KVKK\n\n- [ ] Konum sürekli takip edilmeyecek.\n- [ ] Konum sadece işlem anında alınacak.\n- [ ] Konum alınacak işlemler açıkça belirlenecek.\n- [ ] Konum izni reddedilirse bu durum loglanacak.\n- [ ] Personel ilk girişte bilgilendirme metni görecek.\n- [ ] Personel onayı kayıt altına alınacak.\n- [ ] Konum kaydında enlem, boylam, doğruluk, tarih, kullanıcı, görev, IP ve user agent tutulacak.\n- [ ] Konum verisi sadece yetkili kullanıcılar tarafından görülebilecek.\n- [ ] Personel başka personelin konum kayıtlarını göremeyecek.\n\n### 2.8 Veritabanı ve Migration Güvenliği\n\n- [x] SQLite foreign key desteği aktif edilecek.\n- [x] SQLite WAL modu kullanılacak.\n- [x] SQLite busy timeout ayarlanacak.\n- [x] Alembic migration altyapısı kurulacak.\n- [x] Baseline schema oluşturulacak.\n- [x] Baseline tablo kontrol komutu eklenecek.\n- [ ] Migration öncesi otomatik yedekleme eklenecek.\n- [ ] Backup standardı belirlenecek.\n- [ ] Backup doğrulama sistemi eklenecek.\n- [ ] Restore testi eklenecek.\n- [ ] Canlı veride destructive migration kontrollü yapılacak.\n- [ ] Soft delete yaklaşımı kritik tablolarda uygulanacak.\n\n### 2.9 Konfigürasyon ve Secret Güvenliği\n\n- [x] `.env` dosyası git dışında tutulacak.\n- [ ] Production ortamda debug kapalı olacak.\n- [ ] Production ortamda güçlü `SECRET_KEY` zorunlu olacak.\n- [ ] Varsayılan admin şifresiyle teslim yapılmayacak.\n- [ ] Kurulum teslim raporunda şifre açık yazılmayacak.\n- [ ] Loglarda token veya şifre görünmeyecek.\n- [ ] GitHub'a veritabanı, upload dosyası veya secret gitmeyecek.\n- [ ] Production güvenlik kontrol komutu yazılacak.\n\n---\n\n## 3. Her Yeni Özellik İçin Zorunlu Sorular\n\nHer yeni endpoint, servis veya modül için şu sorular cevaplanacaktır:\n\n- Bu endpoint kim tarafından kullanılabilir?\n- Personel başka işletmenin verisine erişebilir mi?\n- Personel başka personelin verisine erişebilir mi?\n- Bu işlem `business_id` filtresi gerektiriyor mu?\n- Bu işlem audit log gerektiriyor mu?\n- Bu işlem rate limit gerektiriyor mu?\n- Bu veri hassas mı?\n- Bu veri response içinde dönmeli mi?\n- Bu işlem soft delete mi olmalı?\n- Bu işlem için test yazıldı mı?\n- Hata durumunda teknik detay sızıyor mu?\n- Production ortamda bu özellik güvenli çalışır mı?\n\n---\n\n## 4. Güvenlik Testleri\n\nMissio güvenlik testleri şu gruplarda ilerleyecektir:\n\n- Auth testleri\n- Token testleri\n- Rol yetki testleri\n- Business scope testleri\n- Personel veri izolasyonu testleri\n- Brute-force testleri\n- Audit log testleri\n- Dosya yükleme güvenliği testleri\n- Konum izni ve konum log testleri\n- Production config testleri\n\n---\n\n## 5. Güvenlik Tamamlanma Kriteri\n\nBir modül şu koşullar sağlanmadan tamamlanmış sayılmaz:\n\n- Endpoint çalışıyor.\n- Yetki kontrolü var.\n- Business scope kontrolü var.\n- Gerekli audit log var.\n- Input validation var.\n- Hassas veri sızdırmıyor.\n- Hata cevapları güvenli.\n- Testleri yazılmış.\n- Testleri geçiyor.\n\n---\n\n## 6. Mevcut Güvenlik İlerleme Durumu\n\nMevcut durumda tamamlanan temel güvenlik parçaları:\n\n- Parola hash sistemi\n- Parola güç politikası\n- Rol sabitleri\n- JWT access token temeli\n- Token doğrulama testleri\n- Kullanıcı repository temeli\n- Auth service temeli\n- Kullanıcı oluşturma ve doğrulama testleri\n- SQLite güvenli bağlantı ayarları\n- Alembic migration altyapısı\n- Baseline schema kontrol komutu\n\nSıradaki güvenlik adımı:\n\n> ADIM 5D — Login attempt, brute-force koruması ve auth audit log.\n"
README_SECURITY_SECTION = "## Güvenlik Kapısı / Security Gate\n\nMissio; personel, görev, konum, fotoğraf kanıtı, işlem geçmişi ve rapor verileri tuttuğu için güvenlik ilk sürümden itibaren P0 zorunluluğudur.\n\nAna güvenlik kuralı:\n\n> Özellik çalışıyor diye tamamlanmış sayılmaz. Güvenlik kontrolü ve testi yoksa özellik tamamlanmış değildir.\n\nGüvenlik kapısı tamamlanmadan görev modülü, fotoğraf kanıtı, raporlama ve frontend cilasına geçilmeyecektir.\n\nZorunlu güvenlik başlıkları:\n\n- Şifreler güvenli hash yöntemi ile saklanacaktır.\n- Zayıf şifreler kabul edilmeyecektir.\n- JWT access token yapısı kontrollü kullanılacaktır.\n- Production ortamda güçlü secret key zorunlu olacaktır.\n- Login attempt ve brute-force koruması eklenecektir.\n- Başarılı ve başarısız login işlemleri audit log'a yazılacaktır.\n- Personel sadece kendi görevlerini görebilecektir.\n- Yönetici ve patron sadece kendi işletmesine ait verileri görebilecektir.\n- Her işletme verisi için `business_id` izolasyonu zorunludur.\n- Pasif modüller sadece arayüzde değil, backend seviyesinde de kapatılacaktır.\n- Kritik işlemler audit log'a yazılacaktır.\n- Konum sürekli takip edilmeyecek, sadece işlem anında alınacaktır.\n- Fotoğraf yükleme sistemi dosya güvenliği kurallarıyla korunacaktır.\n- API response içinde `password_hash`, secret veya gereksiz hassas veri dönmeyecektir.\n- Production ortamda debug kapalı olacaktır.\n- `.env`, veritabanı, upload dosyaları ve secret bilgileri GitHub'a gönderilmeyecektir.\n- Güvenlik testleri yazılmadan özellik tamamlanmış sayılmayacaktır.\n\nDetaylı güvenlik kontrol listesi:\n\n```text\ndocs/SECURITY_CHECKLIST.md\n```\n"

START_MARKER = "<!-- MISSIO_SECURITY_GATE_START -->"
END_MARKER = "<!-- MISSIO_SECURITY_GATE_END -->"


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Dosya bulunamadi: {path}")

    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_marked_section() -> str:
    return (
        f"{START_MARKER}\n"
        f"{README_SECURITY_SECTION.rstrip()}\n"
        f"{END_MARKER}\n"
    )


def update_readme_security_section(content: str) -> str:
    marked_section = build_marked_section()

    if START_MARKER in content and END_MARKER in content:
        pattern = re.compile(
            rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}\n?",
            re.DOTALL,
        )
        return pattern.sub(marked_section + "\n", content)

    insert_before_candidates = [
        "## 22. KVKK ve Personel Bilgilendirme Yaklaşımı",
        "## 23. Bildirim Mantığı",
        "## 24. Teknoloji Yığını",
        "## 29. Yol Haritası",
    ]

    for candidate in insert_before_candidates:
        index = content.find(candidate)

        if index != -1:
            before = content[:index].rstrip()
            after = content[index:].lstrip()
            return before + "\n\n" + marked_section + "\n" + after

    return content.rstrip() + "\n\n" + marked_section


def update_progress(content: str) -> str:
    progress_pattern = re.compile(
        r"(Proje ilerleme durumu:\s*\n\n```text[^`]*\n)(%?\d+)(\n```)",
        re.IGNORECASE,
    )

    if progress_pattern.search(content):
        return progress_pattern.sub(r"\g<1>%31\g<3>", content, count=1)

    return content


def main() -> None:
    readme_content = read_text(README_PATH)
    readme_content = update_readme_security_section(readme_content)
    readme_content = update_progress(readme_content)

    write_text(README_PATH, readme_content)
    write_text(SECURITY_PATH, SECURITY_CHECKLIST)

    print("README.md guvenlik kapisi bolumu guncellendi.")
    print("docs/SECURITY_CHECKLIST.md olusturuldu/guncellendi.")
    print("Tamamlandi.")


if __name__ == "__main__":
    main()
