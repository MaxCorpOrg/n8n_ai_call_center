# 01. Инфраструктура и рабочие пространства

## 1) Реестр серверов

| Сервер | IP-адрес | Локация | Назначение | ОС | CPU | RAM | Диск | Статус |
|---|---|---|---|---|---|---|---|---|
| ai-core-1 | 147.45.213.87 | TODO | n8n + Traefik + automation | Ubuntu 24.04 | TODO | TODO | TODO | active |

Примечание: IP подтверждён в `docker-compose.ip.yml`.

## 2) Сетевая архитектура

| Компонент | Значение | Примечание |
|---|---|---|
| SSH | `22/tcp` | Только по ключам, user `aicore` |
| HTTP | `80/tcp` | Traefik / Let's Encrypt |
| HTTPS | `443/tcp` | Публичный вход в n8n |
| n8n internal | `5678` | Внутри compose-сети |
| UFW | enabled | Минимально открытые порты |

### Маршрутизация и периметр
- Edge: `Traefik` (TLS termination).
- App: `n8n` container.
- Дополнительно: `postgres` в call-center compose override.

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
| media_orchestrator_v1 | `n8n_workspaces/media_orchestrator_v1` | Телеграм-оркестратор контента | `C8Wmmjuv5hC425PM`, `ABnHZb9Ee2YOtfr2`, `KeKhk230Zy3Iz0a4`, `LG1KGfhnNCICjNra`, `KFWMYCaEpWAdVIn3`, `DUJBo0tvHA5qIafi` |

## 5) Облака / контейнеры / VM (шаблон)

| Тип | Имя | Runtime | Размер | Зона | Ответственный |
|---|---|---|---|---|---|
| Container | n8n | Docker | TODO | TODO | TODO |
| Container | traefik | Docker | TODO | TODO | TODO |
| Container | postgres (optional) | Docker | TODO | TODO | TODO |
