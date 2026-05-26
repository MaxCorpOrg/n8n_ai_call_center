# Агент-Сыщик Косметологов

Этот комплект превращает текущий ручной сбор контактов в управляемый агент для `n8n` и Telegram.

## Что входит
- локальный сервис поиска и выгрузки: `/home/max/n8n_ai_call_center/scripts/cosmetologist_hunter_service.py`
- запускной wrapper: `/home/max/n8n_ai_call_center/scripts/run_cosmetologist_hunter_service.sh`
- черновик systemd unit: `/home/max/n8n_ai_call_center/deploy/systemd/cosmetologist_hunter.service.example`
- server bootstrap инструментов: `/home/max/n8n_ai_call_center/scripts/deploy_server_scrape_tooling.sh`
- server browser client launch: `/home/max/n8n_ai_call_center/scripts/run_site_control_browser_client.sh`
- системный промпт агента: `/home/max/n8n_ai_call_center/prompts/cosmetologist_hunter/telegram_controller_system_prompt_ru.md`
- импортируемый `n8n` workflow: `/home/max/n8n_ai_call_center/workflows/COSMETOLOGIST_HUNTER_TELEGRAM_DRAFT.json`
- серверные пути и tool-layer: `/home/max/n8n_ai_call_center/docs/cosmetologist_hunter_agent/06_SERVER_TOOLING_RU.md`

## Что делает система
1. Telegram-бот принимает команду или обычное текстовое сообщение.
2. Mistral интерпретирует намерение: показать настройки, поменять город, поменять лимит или запустить поиск.
3. `n8n` вызывает локальный сервис `cosmetologist_hunter_service.py`.
4. Сервис ищет новые контакты косметологов по источникам `Prodoctorov`, `Yandex Maps` и `2GIS`.
   Для задачи частных косметологов текущий live-режим сначала берёт врачебные профили и отсекает клиники/центры/салоны до записи результата.
5. Для загрузки страниц сервис может использовать серверный `Firecrawl`, а при необходимости и `site-control-kit` как browser fallback.
   Серверный browser client рекомендуется запускать `on-demand` перед реальным browser fallback, а не держать 24/7.
6. Результат записывается в новую Google-таблицу и в локальный `.xlsx` в формате вашего call center.
7. Telegram возвращает ссылку на Google Sheets и путь к локальному файлу.

## Базовые возможности
- выбор города
- выбор количества контактов
- нумерация таблиц по схеме `контакты_косметологов_<город>_<номер>` с продолжением от уже существующих таблиц на Google Drive
- дедупликация по телефонам against исходный лист и уже созданные таблицы по тому же городу
- дедупликация по `phone_primary`, `phone_secondary`, названию компании и связке `название + адрес`
- жёсткий приоритет именно на косметологов, а не случайные салоны красоты
- private-only фильтр для частных косметологов Москвы: `doctor_profile`, `private_keyword` или имя специалиста, без clinic/company results
- endpoint диагностики инструментов: `GET /tooling/status`
- endpoint трассировки fetch-слоя: `GET /debug/fetch-trace?limit=20`
- endpoint debug summary: `GET /debug/summary?chat_id=<id>&estimate_cap=30&refresh=1`
- рекомендуемый `site-control` client id: `client-cosmetologist-browser`

## Минимальный сценарий запуска
1. Заполнить `/home/max/n8n_ai_call_center/.env.cosmetologist_hunter` по образцу из `.env.cosmetologist_hunter.example`.
2. Запустить локальный сервис.
3. Импортировать workflow в `n8n`.
4. Привязать в workflow credential для Telegram-бота и credential для Mistral.
5. Активировать workflow.

## Telegram-команды
- `/start`
- `/help`
- `/settings`
- `/city Москва`
- `/count 45`
- `найди 30 косметологов в Казани`
- `запусти поиск по Москве на 60 контактов`

## Формат результата
Сервис сохраняет лист в таком же формате, как ваш текущий шаблон call center:
- лист `Лиды_обзвон`
- те же колонки `A:AM`
- совместимость с текущим обзвоном и постобработкой

## Последний проверенный результат
- Дата: `2026-05-25`
- Режим: частные косметологи, Москва
- Google Sheet: `https://docs.google.com/spreadsheets/d/14X6j699O5J_RtjfUZ4JDddugisbIV0XdAr3HFP5a2kg/edit`
- Последний файл на 50 строк: `/home/max/n8n_ai_call_center/ Таблицы_контактов /контакты_косметологов_москва_50.xlsx`
- Preview 50 строк: `/home/max/n8n_ai_call_center/.runtime/cosmetologist_hunter/previews/контакты_косметологов_москва_50.json`
- Лог сборки 50 строк: `/home/max/n8n_ai_call_center/.runtime/cosmetologist_hunter/logs/2026-05-25_private_cosmetologists_50_build.log`
- Строгий live-прогон с Google Sheet дал 5 проверенных врачебных контактов: `/home/max/n8n_ai_call_center/ Таблицы_контактов /контакты_косметологов_москва_49.xlsx`
- Live Prodoctorov после серии запросов начал отдавать ограничение доступа; поэтому `_50.xlsx` собран как private-practice кандидатная база из результатов агента и требует ручной QA нижних строк, если нужен только формат “ФИО частного врача”.
