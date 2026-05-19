# Missio Business Creation

Bu doküman super admin ile işletme oluşturma ve ilk patron hesabı açma modelini açıklar.

---

## Akış

1. İlk kurulumda `super_admin` oluşturulur.
2. `super_admin` müşteri işletmesini oluşturur.
3. İşletmeye ilk patron hesabı açılır.
4. Patron hesabı `boss` rolüyle ilgili `business_id` kapsamına bağlanır.
5. İşletme ve patron oluşturma işlemleri audit log'a yazılır.

---

## Güvenlik Kuralları

- Sadece `super_admin` işletme oluşturabilir.
- İşletme `slug` benzersiz olmalıdır.
- İşletme sahibi şifresi parola politikasına uymalıdır.
- İşletme sahibi varsayılan rolü `boss` olur.
- Şifre hiçbir audit log içinde yazılmaz.
- `business.created` audit log kaydı oluşturulur.
- `business.owner_created` audit log kaydı oluşturulur.

---

## Komut

Etkileşimli şifre girişiyle kullanım:

```powershell
cd C:\missio\backend
python -m app.commands.create_business_with_owner --super-admin-username mustafa --business-name "Ertan Market" --business-slug "ertan-market" --owner-full-name "Ertan Market Patron" --owner-username ertan
```

Parametreli kullanım:

```powershell
python -m app.commands.create_business_with_owner --super-admin-username mustafa --business-name "Ertan Market" --business-slug "ertan-market" --owner-full-name "Ertan Market Patron" --owner-username ertan --owner-password "GüçlüŞifre.2026!" --yes
```

Not: Parametreli kullanım terminal geçmişinde şifre bırakabilir. Gerçek kurulumda etkileşimli kullanım daha güvenlidir.

---

## Kontrol

```powershell
python -m app.commands.check_business_creation
```

---

## Security Gate Entegrasyonu

Business creation kontrolü merkezi güvenlik kapısına eklenmiştir:

```powershell
python -m app.commands.check_security_gate
```
