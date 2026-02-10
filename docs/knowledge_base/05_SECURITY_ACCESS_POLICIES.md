# 05. Безопасность и доступ

## 1) Политика доступа

| Уровень | Кто | Доступ |
|---|---|---|
| Owner | Владелец проекта | Полный |
| Admin | Инженеры платформы | По необходимости |
| User | Конечные пользователи | Только через Telegram бота |

## 2) Актуальные меры
- SSH: root-login выключен, парольная аутентификация выключена.
- UFW: открыты только `22`, `80`, `443`.
- Доступ к Telegram-боту ограничен в master workflow по `chat_id/user_id`.

### Параметры access control (n8n)
| Workflow | Узел | Политика |
|---|---|---|
| `C8Wmmjuv5hC425PM` | `Access Control` + `Access Switch` | Пропуск только owner IDs |

## 3) Управление секретами
- Не хранить токены/API-ключи в Markdown.
- Секреты только в n8n Credentials / `.env` с ограниченными правами.
- Ротация ключей: минимум раз в 90 дней или после инцидента.

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
```
