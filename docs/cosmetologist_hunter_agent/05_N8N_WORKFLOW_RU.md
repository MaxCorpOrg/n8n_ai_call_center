# Workflow n8n

Файл:
- `/home/max/n8n_ai_call_center/workflows/COSMETOLOGIST_HUNTER_TELEGRAM_DRAFT.json`

## Что делает workflow
- принимает сообщение из Telegram
- отсекает voice input
- обогащает контекст `chat_id` и `text`
- через Mistral определяет действие
- вызывает локальный сервис поиска
- возвращает ответ обратно в Telegram

## Основные маршруты
- `help`
- `get_settings`
- `set_settings`
- `run_search`

## Почему workflow сделан draft-форматом
В репозитории безопаснее хранить его без живых credential. После импорта в `n8n` остаётся только привязать секреты и активировать.

## Что менять чаще всего
- prompt агента
- URL локального сервиса
- текст welcome/help сообщения
- модель Mistral
