# 09. Состояние проекта и последние изменения

## 1) Актуальное состояние (оперативный снимок)
- Проект: `n8n_ai_call_center`.
- Базовая инфраструктура: Ubuntu 24.04 + Docker + Traefik + HTTPS.
- Memory-слой: `postgres_memory` + `postgrest` + таблица `agent_memory`.
- DB UI: `adminer` (через Traefik на 443, с BasicAuth).
- Основной workspace: `media_orchestrator_v1`.
- Telegram-оркестратор: `C8Wmmjuv5hC425PM`.

## 2) Последние важные изменения

### 2026-02-12 — Postgres Memory stack + API
- Добавлены файлы:
  - `docker-compose.memory.yml`,
  - `.env.memory.example`,
  - `sql/002_agent_memory.sql`.
- Поднят отдельный memory-контур:
  - `postgres_memory` (`postgres:16-alpine`),
  - `postgrest` (`postgrest/postgrest:latest`).
- В SQL-инициализации добавлены:
  - таблица `agent_memory`,
  - индексы по `session_id`/`agent_id`,
  - trigger `updated_at`,
  - роль `web_anon` для PostgREST.

### 2026-02-12 — Adminer UI через HTTPS (Traefik)
- Добавлен `docker-compose.adminer.yml`.
- Добавлены env в `.env.https.example`:
  - `ADMINER_DOMAIN`,
  - `ADMINER_BASICAUTH`.
- Цель: визуальный доступ к PostgreSQL в браузере без работы из CLI.

### 2026-02-12 — Стабилизация Master агента
- В `C8Wmmjuv5hC425PM`:
  - убран `Window Buffer Memory`,
  - добавлен `Postgres Chat Memory` (таблица `agent_memory`, `contextWindowLength=20`),
  - добавлен встроенный `Router | Intent Parse` перед `AGENT 1 | Manager`,
  - добавлен `Reply Guardrail` для rewrite отказов и цикловых ответов,
  - подключён tool `Memory Neuro Agent`,
  - удалён внешний `Intent Router | Tool` из цепочки мастера.
- Эффект:
  - меньше “залипаний” в уточнениях,
  - устойчивее обработка прямых image/video запросов,
  - контекст диалога хранится в PostgreSQL.

### 2026-02-11 — Добавлен Memory Neuro Agent
- Создан workflow: `kcH2rlqr8aZoOPiO` (`MEMORY_NEURO_AGENT | GitHub Markdown Memory (draft)`).
- Назначение:
  - долговременная память в markdown-файлах GitHub-репозитория `MaxCorpOrg/memory`;
  - действия `upsert/read/search/list_files/archive_weekly/compact/sync/health_check`;
  - еженедельное архивирование и compact-режим при превышении лимитов;
  - connector-режим для `gdrive/dropbox/s3` через внешние endpoint URL.
- Требуемые env для n8n:
  - `MEMORY_GITHUB_TOKEN` (required для backend `github`),
  - `MEMORY_CONNECTOR_GDRIVE_URL` / `MEMORY_CONNECTOR_DROPBOX_URL` / `MEMORY_CONNECTOR_S3_URL` (optional),
  - `MEMORY_CONNECTOR_AUTH_TOKEN` (optional).

### 2026-02-11 — Memory Brain (intent/router слой в memory workflow)
- В `kcH2rlqr8aZoOPiO` добавлен узел `Memory Brain` между `Set Config` и `Validate Config`.
- Что делает:
  - нормализует действие (`upsert/search/get_file/list_files/archive_weekly/compact/sync`);
  - определяет backend (`github/gdrive/dropbox/s3`) по явному параметру и по тексту;
  - формирует `memory_key`, priority и confidence;
  - добавляет мягкие guardrails (например, small-talk не пишет в память как `upsert`).
- В ответ добавлены поля `brain`, `brain_confidence`, `brain_priority`, `brain_warnings` для отладки и контроля в Agent 1.

### 2026-02-10 — Добавлен KB Sync Agent
- Создан workflow: `K5es5hBE05LEeB1j` (`KB_SYNC_AGENT | Knowledge Base Sync (draft)`).
- Функции:
  - проверка свежести `docs/knowledge_base` по git-коммитам;
  - автообновление `docs/knowledge_base/09_PROJECT_CHANGELOG_AND_STATE.md` через GitHub API;
  - Telegram-уведомление о результате синхронизации.
- Требуемые env для n8n:
  - `KB_GITHUB_TOKEN` (required),
  - `N8N_PUBLIC_API_KEY` (optional, для статистики workflow).

### 2026-02-10 — Рефактор архитектуры агента (база для текущего роутинга)
- Добавлен workflow `ABnHZb9Ee2YOtfr2` (`MEDIA_AGENT_ROUTER | Intent Router (draft)`).
- Логика интентов вынесена из монолитного промпта в отдельный модуль (Code + Switch).
- Позже часть логики была встроена обратно в Master (`Router | Intent Parse`) для линейной и детерминированной обработки.

### 2026-02-10 — Доступ к Telegram-боту ограничен
- В `C8Wmmjuv5hC425PM` добавлены узлы:
  - `Access Control`
  - `Access Switch`
  - `Set Unauthorized Reply`
- Политика: owner-only доступ (по chat_id/user_id).

### 2026-02-10 — Улучшен pipeline генерации
- Agent 5 переведён на надёжный сценарий отправки фото в Telegram (`sendPhoto` через ноду Telegram).
- Поддержка Flow/Vertex-конфигурации и fallback на Pollinations.

### 2026-02-10 — Диалоговый режим и video-first
- Agent 1: поддержка guided + prompt-ready режима.
- Agent 2: усилен image->video planning.
- Приоритет конечной цели: создание видео, а не только изображения.

## 3) Последние коммиты (из git log)
| Commit | Сообщение |
|---|---|
| `9e3b8bb` | feat: add postgres memory stack, adminer access, and media-agent stability updates |
| `49f69ed` | Переведен мастер-агент в свободный режим диалога и усилена устойчивость |
| `3522fd9` | Добавлен KB Sync Agent и обновлено рабочее пространство медиа-оркестратора |
| `f13e4a6` | Рефактор n8n-агента: Intent Router, маршрутизация и обновление workspace |
| `8616d93` | Добавлен переносимый workspace для медиа-оркестратора n8n |

## 4) Текущие риски / TODO
- [ ] Заполнить реальные характеристики железа сервера.
- [ ] Зафиксировать финальные каналы алертов и SLA.
- [ ] Настроить регулярные учебные тесты восстановления backup.
- [ ] Поддерживать owner ID list в Access Control при смене админов.
- [ ] Проверить и зачистить workflow JSON от тестовых/временных API-ключей перед внешними публикациями.
- [ ] Принять финальное решение по внешней доступности `5432/3000` (закрыть UFW или оставить только internal).

## 5) Шаблон журналирования изменений
```md
### YYYY-MM-DD HH:MM UTC — Изменение
- Что изменено:
- Какие файлы/workflow:
- Риски:
- Проверка:
- Следующие шаги:
```
