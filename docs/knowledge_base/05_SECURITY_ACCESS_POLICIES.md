# 05. Безопасность и доступ

## 1) Политика доступа

| Уровень | Кто | Доступ |
|---|---|---|
| Owner | Владелец проекта | Полный |
| Admin | Инженеры платформы | По необходимости |
| User | Конечные пользователи | Только через Telegram бота |

## 2) Актуальные меры
- SSH:
  - старое базовое описание: `root-login выключен, парольная аутентификация выключена`;
  - актуальная операционная реальность по отчёту: вход на прод-сервер `147.45.213.87` выполняется через `ssh root@147.45.213.87`;
  - на момент последней локальной проверки рабочий SSH-ключ с машины `max` не подтверждён, сервер отвечал `Permission denied (publickey,password,keyboard-interactive)`;
  - значит следующий безопасный шаг: перевести этот доступ на отдельный deploy/admin key и убрать зависимость от ручного root-пароля.
- UFW: открыты только `22`, `80`, `443`.
- Доступ к Telegram-боту ограничен в master workflow по `chat_id/user_id`.
- `.env.https` и `.env.memory` не коммитятся (`.gitignore`).
- Adminer публикуется через Traefik + HTTPS + BasicAuth (`ADMINER_BASICAUTH`).

### Параметры access control (n8n)
| Workflow | Узел | Политика |
|---|---|---|
| `C8Wmmjuv5hC425PM` | `Access Control` + `Access Switch` | Пропуск только owner IDs |

### Внешние точки доступа
| Точка | Режим | Статус |
|---|---|---|
| n8n UI/API | `https://${DOMAIN_NAME}` | public |
| Adminer UI | `https://${ADMINER_DOMAIN}` (рекомендовано) | protected (BasicAuth) |
| Postgres `5432` | Только internal/ops | не публиковать в интернет |
| PostgREST `3000` | Только internal/ops | не публиковать в интернет |

## 3) Управление секретами
- Не хранить токены/API-ключи в Markdown.
- Секреты только в n8n Credentials / `.env` с ограниченными правами.
- Root-пароль сервера `147.45.213.87` не хранить в репозитории и не передавать в handoff-файлах.
- Ротация ключей: минимум раз в 90 дней или после инцидента.
- После импорта workflow проверить и убрать любые тестовые ключи/плейсхолдеры.

## 4) Патчи и уязвимости
- Ежедневный watchlist по GitHub releases/security advisories.
- Для HIGH/CRITICAL: оценка риска в тот же день.
- Обновление через runbook: backup -> update -> smoke test -> monitor.

## 5) Сканы уязвимостей (шаблон)
```bash
# Docker image scan (пример)
trivy image docker.n8n.io/n8nio/n8n:2.6.4

# OS package updates
sudo apt update && sudo apt list --upgradable

# Базовая проверка утечки ключей в repo
rg -n "AIza|AQ\\.|Bearer\\s+[A-Za-z0-9\\-_]+" n8n_workspaces docs -S
```
