#!/usr/bin/env bash
set -euo pipefail

# 1) Добавляем все файлы (кроме тех, что в .gitignore)
git add .

# 2) Делаем коммит с таймстампом
COMMIT_MSG="Update configs $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$COMMIT_MSG" || {
  echo "Нет новых изменений для коммита."
  exit 0
}

# 3) Отправляем в основную ветку main на origin
git push origin main

echo "Успешно задеплоено: $COMMIT_MSG"
