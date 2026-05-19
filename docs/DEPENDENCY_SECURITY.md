# Missio Dependency Security

Bu doküman Missio dependency güvenliği ve parola hash bağımlılığı kararlarını açıklar.

---

## 1. Karar

Missio artık parola hash işlemleri için `passlib` kullanmaz.

Bunun yerine doğrudan `bcrypt` paketi kullanılır.

Sebep:

- Security gate çıktılarında passlib/bcrypt uyumluluk uyarısı görünüyordu.
- Hash/verify işlemi için daha küçük ve net dependency yüzeyi tercih edildi.
- Güvenlik kapısı çıktısında traceback benzeri gürültü olmamalıdır.

---

## 2. Aktif Parola Hash Yaklaşımı

Dosya:

```text
backend/app/core/security.py
```

Kullanılan fonksiyonlar:

```text
hash_password()
verify_password()
validate_password_strength()
is_password_strong()
```

Hash algoritması:

```text
bcrypt
```

---

## 3. Dependency Health Kontrolü

Komut:

```powershell
cd C:\missio\backend
python -m app.commands.check_dependency_health
```

Bu komut şunları kontrol eder:

- Zorunlu paketlerin yüklü olması
- Aktif Python yorumlayıcısı
- bcrypt hash/verify çalışma durumu
- Uygulama kodunda `passlib` import kalmaması

---

## 4. Security Gate Entegrasyonu

Dependency health kontrolü merkezi security gate içine eklenmiştir.

Ana komut:

```powershell
python -m app.commands.check_security_gate
```

---

## 5. Not

Bu adım vulnerability scanner yerine geçmez.

İleride release sürecinde ayrıca dependency vulnerability audit adımı değerlendirilecektir.
