# Создание Google Sheet для call-логов (RU)

## 1) Запуск скрипта

```bash
cd /home/max/AI_CORE/n8n-server
./scripts/create_google_sheet_callcenter.py \
  --client-secret '/home/max/гугл/client_secret_565432086278-5cdudpbljg0ods2tlmj92n1kd06gkpkl.apps.googleusercontent.com.json' \
  --seed-csv '/home/max/AI_CORE/колл_центр_доки /Обзвон Воронин Г.П..csv'
```

Если токена нет, скрипт выдаст ссылку OAuth.

## 2) Получение кода

1. Открыть ссылку.
2. Разрешить доступ.
3. Скопировать `code` из URL вида:
   - `http://localhost:8080/?code=...&scope=...`

## 3) Финальный запуск с кодом

```bash
cd /home/max/AI_CORE/n8n-server
./scripts/create_google_sheet_callcenter.py \
  --client-secret '/home/max/гугл/client_secret_565432086278-5cdudpbljg0ods2tlmj92n1kd06gkpkl.apps.googleusercontent.com.json' \
  --auth-code '<ВСТАВЬ_КОД_ИЗ_URL>' \
  --seed-csv '/home/max/AI_CORE/колл_центр_доки /Обзвон Воронин Г.П..csv'
```

Скрипт создаст таблицу, заполнит заголовки, добавит лист `Справочники` и выведет URL.
