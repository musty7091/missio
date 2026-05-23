# Missio Cloud Secrets Notes

## Amaç

Missio Cloud Run backend için production gizli değerleri Google Secret Manager üzerinde tutulacaktır.

## Secret Manager Değerleri

- missio-secret-key
- missio-database-url

## Cloud Run Service Account

Cloud Run servis hesabına şu roller verilmiştir:

- roles/secretmanager.secretAccessor
- roles/cloudsql.client

## Güvenlik Notu

.cloud-secrets klasörü local bilgisayarda kalır.
Bu klasör GitHub'a gönderilmez.

## Sonraki Adım

CLOUD ADIM 16:
Backend image build, Artifact Registry ve Cloud Run deploy.
