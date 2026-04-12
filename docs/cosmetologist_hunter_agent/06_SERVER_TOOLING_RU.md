# Серверные инструменты агента

Этот документ фиксирует серверный tool-layer для агента поиска косметологов.

## Цель

Агент должен уметь искать контакты не только через обычный `requests`, но и через более устойчивые серверные инструменты:
- `Firecrawl` как основной fetch/render слой;
- `site-control-kit` как browser fallback, если нужен живой браузер.

## Канонические пути на сервере

- проект агента: `/home/aicore/n8n-server`
- корень серверных инструментов: `/home/aicore/agent-tools`
- `Firecrawl`: `/home/aicore/agent-tools/firecrawl`
- совместимый bridge: `/home/aicore/n8n-server/scripts/firecrawl_compat_bridge.py`
- `site-control-kit`: `/home/aicore/agent-tools/site-control-kit`
- браузерный рантайм `site-control-kit`: `/home/aicore/.local/share/site-control-kit-browser`
- запускной скрипт браузерного клиента: `/home/aicore/n8n-server/scripts/run_site_control_browser_client.sh`
- env сервиса агента: `/home/aicore/n8n-server/.env.cosmetologist_hunter`
- env хаба `site-control-kit`: `/etc/site-control-kit/hub.env`

## Сетевые адреса по умолчанию

- `Firecrawl`: `http://127.0.0.1:3002`
- `Firecrawl Playwright service`: `http://127.0.0.1:3003/scrape`
- `site-control-kit hub`: `http://127.0.0.1:8765`
- `cosmetologist_hunter`: `http://127.0.0.1:8787`

## Как агент использует инструменты

Логика в [cosmetologist_hunter_service.py](/home/max/n8n_ai_call_center/scripts/cosmetologist_hunter_service.py):

1. Сначала пробует `Firecrawl` для получения `rawHtml/html`.
2. Если `Firecrawl` не дал HTML, пробует `site-control-kit` через подключённый browser client.
3. Только потом падает обратно на прямой `requests`.

Это позволяет сохранить простой контур и при этом переживать защиту динамических сайтов лучше, чем на одном `requests`.

Если полный self-host Firecrawl через `docker compose` временно недоступен, допускается совместимый bridge на `3002`, который работает поверх `playwright-service-ts` из репозитория Firecrawl. Для hunter-сервиса это прозрачно: endpoint остаётся тем же.

## Управляющие переменные окружения

- `COSMETOLOGIST_HUNTER_SERVER_TOOL_ROOT`
- `COSMETOLOGIST_HUNTER_FIRECRAWL_ROOT`
- `COSMETOLOGIST_HUNTER_FIRECRAWL_BASE_URL`
- `COSMETOLOGIST_HUNTER_FIRECRAWL_API_KEY`
- `COSMETOLOGIST_HUNTER_SITE_CONTROL_ROOT`
- `COSMETOLOGIST_HUNTER_SITE_CONTROL_SERVER_URL`
- `COSMETOLOGIST_HUNTER_SITE_CONTROL_TOKEN`
- `COSMETOLOGIST_HUNTER_SITE_CONTROL_CLIENT_ID`

Рекомендуемое значение `COSMETOLOGIST_HUNTER_SITE_CONTROL_CLIENT_ID` для боевого сервера:

`client-cosmetologist-browser`

Шаблон см. в [.env.cosmetologist_hunter.example](/home/max/n8n_ai_call_center/.env.cosmetologist_hunter.example).

## Проверка статуса

У live-сервиса есть endpoint:

`GET /tooling/status`

Пример:

```bash
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8787/tooling/status
```

Он показывает:
- включён ли `Firecrawl`;
- включён ли `site-control-kit`;
- сколько browser clients подключено к хабу;
- какие серверные пути сейчас считаются каноническими.

Для диагностики последнего fetch-контура есть endpoint:

`GET /debug/fetch-trace?limit=20`

Он показывает, каким backend'ом (`direct`, `firecrawl`, `site_control`) агент реально пытался взять страницу и почему мог отбросить ответ (`empty`, `missing_markers`, `blocking_content`).

## Развёртывание

Локальный bootstrap-скрипт:

[deploy_server_scrape_tooling.sh](/home/max/n8n_ai_call_center/scripts/deploy_server_scrape_tooling.sh)

Он:
- копирует `site-control-kit` на сервер;
- ставит Python venv и systemd unit для хаба;
- клонирует `firecrawl/firecrawl`;
- поднимает `Firecrawl` через `docker compose`;
- прописывает env-переменные в сервис агента.

## Важный нюанс по `site-control-kit`

Сам хаб может жить на сервере без проблем, но для реального browser fallback нужен подключённый browser client с загруженным расширением.

Поэтому есть два режима:
- `hub-only`: сервер знает про `site-control-kit`, но клиентов ещё нет;
- `hub+browser`: хотя бы один браузер подключён, и агент может реально дергать команды `navigate`, `wait_selector`, `get_html`.

## Как довести `site-control-kit` до рабочего browser fallback

1. Запустить хаб `site-control-kit`.
2. Поднять серверный браузерный клиент:

```bash
sudo cp /home/aicore/n8n-server/deploy/systemd/site-control-kit-browser.service.example \
  /etc/systemd/system/site-control-kit-browser.service
sudo systemctl daemon-reload
sudo systemctl enable --now site-control-kit-browser.service
```

3. Проверить, что в `GET /tooling/status` появился хотя бы `1` connected client.
4. После этого hunter сможет целиться в клиент `client-cosmetologist-browser`.
