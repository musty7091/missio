# Missio Business User Management

Bu doküman super admin ile işletme kullanıcıları oluşturma modelini açıklar.

---

## Amaç

İlk kurulumda `super_admin` oluşturulur. Sonra `super_admin` işletme oluşturur ve işletmeye patron hesabı açar. Bu adımdan sonra aynı işletmeye `manager` ve `staff` hesapları açılır.

---

## Güvenlik Kuralları

- İşletme kullanıcısı oluşturma işlemini sadece `super_admin` yapabilir.
- İşletme kullanıcıları mutlaka bir `business_id` kapsamına bağlanır.
- `super_admin` rolü işletme kullanıcısı olarak oluşturulamaz.
- İzin verilen işletme rolleri:
  - `boss`
  - `business_owner`
  - `manager`
  - `staff`
- Şifre parola politikasına uymalıdır.
- Şifre audit log'a yazılmaz.
- Her kullanıcı oluşturma işlemi `business.user_created` audit log kaydı üretir.

---

## Komut

Etkileşimli şifre girişiyle kullanım:

```powershell
cd C:\missio\backend
python -m app.commands.create_business_user --super-admin-username mustafa --business-slug "ertan-market" --full-name "Mehmet Personel" --username mehmet --role staff
```

Parametreli kullanım:

```powershell
python -m app.commands.create_business_user --super-admin-username mustafa --business-slug "ertan-market" --full-name "Mehmet Personel" --username mehmet --role staff --password "GüçlüŞifre.2026!" --yes
```

Not: Parametreli kullanım terminal geçmişinde şifre bırakabilir. Gerçek kurulumda etkileşimli kullanım daha güvenlidir.

---

## Kontrol

```powershell
python -m app.commands.check_business_user_management
```

---

## Security Gate Entegrasyonu

Business user management kontrolü merkezi güvenlik kapısına eklenmiştir:

```powershell
python -m app.commands.check_security_gate
```
