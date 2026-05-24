# Missio Cloud SQL Notes

## Amaç

Missio cloud ortamında PostgreSQL veritabanı kullanacaktır.

## Instance

Instance ID: missio-db
Region: europe-west1
Zone: europe-west1-b
Database version: PostgreSQL 16
Edition: Enterprise
Tier: db-f1-micro
Database name: missio_prod
Application user: missio_app

## Bağlantı Kararı

Cloud Run backend, Cloud SQL veritabanına instance connection name üzerinden bağlanacaktır.

Instance connection name:

missio-cloud-cyprus:europe-west1:missio-db

## Local Secret Dosyası

.cloud-secrets/missio-cloud-sql.env

Bu dosya GitHub'a gönderilmeyecektir.

## Veri Taşıma Kararı

Mevcut SQLite verileri test amaçlı olduğu için Cloud SQL'e taşınmayacaktır.
Cloud SQL tarafında temiz veritabanı kullanılacaktır.

## Sonraki Adım

CLOUD ADIM 15:
Cloud SQL bağlantı doğrulama, Secret Manager hazırlığı ve Cloud Run deploy öncesi production env hazırlığı.
