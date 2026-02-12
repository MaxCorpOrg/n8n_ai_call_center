# 04. Мониторинг, алерты, логи, аудит

## 1) Ключевые метрики

| Слой | Метрика | Порог warning | Порог critical |
|---|---|---|---|
| Host | CPU usage | >70% 5m | >90% 5m |
| Host | RAM usage | >80% 5m | >92% 5m |
| Host | Disk `/` | >80% | >90% |
| Host | Network errors | >1% | >3% |
| Docker | Container restart count | >1/час | >3/час |
| n8n | Failed executions ratio | >5% | >15% |
| n8n | Queue/latency webhook | >2s | >5s |
| Postgres memory | Connection errors | >1% | >3% |
| Postgres memory | Storage growth | >2 GB/day | >5 GB/day |
| PostgREST | 5xx rate | >1% | >3% |
| Adminer | HTTPS availability | >1 fail / 5 min | >3 fail / 5 min |

## 2) Оповещения

| Канал | Тип событий | Ответственный |
|---|---|---|
| Telegram ops chat | critical infra + n8n down | SRE on duty |
| Telegram ops chat | postgres_memory/postgrest/adminer down | SRE on duty |
| Email | daily digest + watchlist | Platform owner |

## 3) Логи

| Источник | Команда/путь |
|---|---|
| n8n container logs | `docker compose ... logs -f n8n` |
| traefik logs | `docker compose ... logs -f traefik` |
| postgres_memory logs | `docker compose ... logs -f postgres_memory` |
| postgrest logs | `docker compose ... logs -f postgrest` |
| adminer logs | `docker compose ... logs -f adminer` |
| watchlist reports | `logs/watchlist/` |
| backup logs | `/home/aicore/n8n-backups/*.log` |

## 4) Аудит безопасности
- Проверка SSH конфигурации и ключей.
- Проверка UFW правил.
- Проверка внешней публикации `5432/3000/8080` (должны быть закрыты при работе через 443).
- Проверка релизов и advisory n8n.
- Проверка прав на `.env*` и backup-архивы.

Команды:
```bash
sudo ufw status verbose
sudo grep -E "^(PermitRootLogin|PasswordAuthentication)" /etc/ssh/sshd_config
./scripts/check_n8n_watchlist.sh
ss -tulpen | rg ":(22|80|443|5432|3000|8080)\\b"
```

## 5) Интеграция с Prometheus/Grafana/Zabbix (шаблон)
- Экспорт метрик host через node_exporter.
- Экспорт Docker метрик через cAdvisor.
- Дашборды:
  - Host health,
  - Docker services,
  - n8n execution health,
  - Webhook latency,
  - Postgres memory table growth (`agent_memory`).
