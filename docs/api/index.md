---
owner: Mariia Hutsuliak
status: published
review_date: 2027-02-12
tags: [api]
---

# Довідник API

Ця сторінка **не містить власного опису маршрутів**. Інтерактивна довідка нижче рендериться з єдиного контракту [`openapi.yaml`](openapi.yaml) (OpenAPI 3.0.3) під час збірки сайту. Змінити опис можна лише в цьому файлі, тому довідка не може розійтися з контрактом (Single Source of Truth, єдине джерело істини).

Автентифікація: сесійна cookie Flask-Login. Спочатку потрібно увійти через `/login`.

<swagger-ui src="openapi.yaml"/>

## Пов'язані документи

- [ADR-0004: API-first](../architecture/adr/0004-api-first-openapi-contract.md)
- [SDD](../architecture/sdd.md)
