# 01. Инфраструктура и рабочие пространства

## 1) Реестр серверов

| Сервер | IP-адрес | Локация | Назначение | ОС | CPU | RAM | Диск | Статус |
|---|---|---|---|---|---|---|---|---|
| ai-core-1 | `147.45.213.87` | TODO | n8n + Traefik + memory stack + automation | Ubuntu 24.04 | TODO | TODO | TODO | active |

Примечание:
- IP подтверждён в `docker-compose.ip.yml`.
- Актуальный handoff по этому серверу: `10_SERVER_ACCESS_147_45_213_87.md`.
- Рабочий SSH-вход по выделенному ключу с машины `max` подтверждён через alias `ai-core-prod-147`.

## 2) Сетевая архитектура

| Компонент | Значение | Примечание |
|---|---|---|
| SSH | `22/tcp` | Актуальный операционный вход: `ssh ai-core-prod-147` или `ssh root@147.45.213.87` по выделенному ключу |
| HTTP | `80/tcp` | Traefik redirect -> HTTPS |
| HTTPS | `443/tcp` | Публичный вход в n8n и Adminer (через Traefik) |
| n8n internal | `5678/tcp` | Внутри docker-сети |
| postgres_memory | `5432/tcp` | Опубликован compose; внешне держать закрытым UFW |
| postgrest | `3000/tcp` | Опубликован compose; внешне держать закрытым UFW |
| adminer internal | `8080/tcp` | Внутри контейнера, наружу отдаётся через Traefik 443 |
| UFW | enabled | Базово открыты `22`, `80`, `443` |

### Маршрутизация и периметр
- Edge: `Traefik` (TLS termination, Let's Encrypt).
- App: `n8n` container (`docker-compose.https.yml`).
- Memory layer: `postgres_memory` + `postgrest` (`docker-compose.memory.yml`).
- DB UI: `adminer` (`docker-compose.adminer.yml`).

### Рабочие пути на проде
- Живой рабочий каталог: `/home/aicore/n8n-server`
- Clean deploy-клон: `/home/aicore/n8n-ai-clean`
- Для автодеплоя и git-управляемых правок использовать clean-clone, а не грязный рабочий прод-каталог.

## 3) VPN / DNS (шаблон)

| Параметр | Значение | Статус |
|---|---|---|
| VPN клиент | AdGuard VPN CLI | configured |
| Режим | TUN | configured |
| Локация по умолчанию | TODO | verify |
| DNS через VPN | TODO | verify |

Команды проверки:
```bash
adguardvpn-cli status
curl -s https://api.ipify.org; echo
```

## 4) Рабочие пространства (n8n)

| Workspace | Путь | Назначение | Ключевые workflow |
|---|---|---|---|
| media_orchestrator_v1 | `n8n_workspaces/media_orchestrator_v1` | Телеграм-оркестратор контента + KB Sync + Memory | `C8Wmmjuv5hC425PM`, `ABnHZb9Ee2YOtfr2`, `KeKhk230Zy3Iz0a4`, `KFWMYCaEpWAdVIn3`, `LG1KGfhnNCICjNra`, `DUJBo0tvHA5qIafi`, `K5es5hBE05LEeB1j`, `kcH2rlqr8aZoOPiO` |

### Локальные рабочие материалы рядом с core-проектом
- В repo-root есть дополнительные рабочие каталоги и артефакты:
  - `agent_contact_parser_docs/`
  - `MANGO_отчеты/`
  - `Документация по скриптам `
  - ` Таблицы_контактов `
  - `workflows/Peptide_Expert_YJdwp45LI1dmrsLy_runtime_2026-03-02.json`
- Это не основной runtime прод-сервера, но это полезные материалы для следующих агентов.
- Подробное описание и правила обращения: `11_LOCAL_WORKING_MATERIALS.md`.

## 5) Контейнеры (оперативный список)

| Тип | Имя сервиса | Файл | Назначение |
|---|---|---|---|
| Container | `traefik` | `docker-compose.https.yml` | TLS, reverse proxy |
| Container | `n8n` | `docker-compose.https.yml` | Оркестратор workflow |
| Container | `redis` | `docker-compose.https.yml` | Вспомогательное хранилище |
| Container | `postgres_memory` | `docker-compose.memory.yml` | Chat memory storage |
| Container | `postgrest` | `docker-compose.memory.yml` | REST API поверх Postgres |
| Container | `adminer` | `docker-compose.adminer.yml` | Визуальный UI для SQL |
