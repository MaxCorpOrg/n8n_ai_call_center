# 09. Состояние проекта и последние изменения

## 1) Актуальное состояние (оперативный снимок)
- Проект: `n8n_ai_call_center`.
- Базовая инфраструктура: Ubuntu 24.04 + Docker + Traefik + HTTPS.
- Основной workspace: `media_orchestrator_v1`.
- Telegram-оркестратор: `C8Wmmjuv5hC425PM`.

## 2) Последние важные изменения

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

### 2026-02-11 — Memory Brain (intent/router слой)
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

### 2026-02-10 — Рефактор архитектуры агента
- Добавлен Intent Router workflow: `ABnHZb9Ee2YOtfr2`.
- В Master подключён `Intent Router | Tool`.
- Логика маршрутизации вынесена из монолитного промпта в отдельный модуль (Code + Switch).

### 2026-02-12 — Intent Router объединён с Master
- В `C8Wmmjuv5hC425PM` добавлен встроенный узел `Intent PreRouter (Merged)`.
- Текущая цепочка обработки текста: `Set Text -> Intent PreRouter (Merged) -> AGENT 1`.
- Внешний tool-узел `Intent Router | Tool` убран из Master, чтобы маршрутизация выполнялась детерминированно до LLM.
- Эффект:
  - стабильная фиксация движка (`FLOW`/`Pollinations`);
  - меньше циклов уточнения и меньше риска потери выбранного движка;
  - сохранена анти-отказ логика (`NO_REFUSAL_MODE` + `Reply Guardrail`).

### 2026-02-12 — Master разделён на 2 агента + Switch Intent внутри
- Полный роутинг-слой (`Router | Intent Parse`, `Router | Switch Intent`, `Router | Route *`) перенесён в `C8Wmmjuv5hC425PM`.
- Добавлен `AGENT 1A | Dialog` (без tools) для живого общения и уточнений.
- `AGENT 1 | Manager` стал фактическим `Tool Executor` (этапы генерации через tools).
- Текущая логика:
  - `Set Text -> Router | Intent Parse -> Router | Switch Intent`
  - `Greeting/Engine/Config/Other -> AGENT 1A | Dialog`
  - `ImageRequest/ConfirmPhoto/Regenerate/ConfirmVideo -> AGENT 1 | Manager`

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
| `f13e4a6` | Рефактор n8n-агента: Intent Router, маршрутизация и обновление workspace |
| `8616d93` | Добавлен переносимый workspace для медиа-оркестратора n8n |
| `3b35551` | Добавлен watchlist по релизам и уязвимостям n8n |
| `46d0273` | Усилена продакшн-конфигурация и CI деплой |

## 4) Текущие риски / TODO
- [ ] Заполнить реальные характеристики железа сервера.
- [ ] Зафиксировать финальные каналы алертов и SLA.
- [ ] Настроить регулярные учебные тесты восстановления backup.
- [ ] Поддерживать owner ID list в Access Control при смене админов.

## 5) Шаблон журналирования изменений
```md
### YYYY-MM-DD HH:MM UTC — Изменение
- Что изменено:
- Какие файлы/workflow:
- Риски:
- Проверка:
- Следующие шаги:
```
