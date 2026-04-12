# Агент-Сыщик Косметологов

Этот комплект превращает текущий ручной сбор контактов в управляемый агент для `n8n` и Telegram.

## Что входит
- локальный сервис поиска и выгрузки: `/home/max/n8n_ai_call_center/scripts/cosmetologist_hunter_service.py`
- запускной wrapper: `/home/max/n8n_ai_call_center/scripts/run_cosmetologist_hunter_service.sh`
- черновик systemd unit: `/home/max/n8n_ai_call_center/deploy/systemd/cosmetologist_hunter.service.example`
- системный промпт агента: `/home/max/n8n_ai_call_center/prompts/cosmetologist_hunter/telegram_controller_system_prompt_ru.md`
- импортируемый `n8n` workflow: `/home/max/n8n_ai_call_center/workflows/COSMETOLOGIST_HUNTER_TELEGRAM_DRAFT.json`

## Что делает система
1. Telegram-бот принимает команду или обычное текстовое сообщение.
2. Mistral интерпретирует намерение: показать настройки, поменять город, поменять лимит или запустить поиск.
3. `n8n` вызывает локальный сервис `cosmetologist_hunter_service.py`.
4. Сервис ищет новые контакты косметологов по источникам `2GIS` и `Yandex Maps`.
5. Результат записывается в новую Google-таблицу и в локальный `.xlsx` в формате вашего call center.
6. Telegram возвращает ссылку на Google Sheets и путь к локальному файлу.

## Базовые возможности
- выбор города
- выбор количества контактов
- нумерация таблиц по схеме `контакты_косметологов_<город>_<номер>` с продолжением от уже существующих таблиц на Google Drive
- дедупликация по телефонам against исходный лист и уже созданные таблицы по тому же городу
- жёсткий приоритет именно на косметологов, а не случайные салоны красоты

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
