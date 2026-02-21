tool-workflow;MEDIA_AGENT_5 | Gemini Nano Banana Image (draft)
set -euo pipefail

# Определяем текущую ветку
BRANCH=$(git symbolic-ref --short HEAD)

# Добавляем всё в индекс
git add .

# Делаем коммит с таймстампом
COMMIT_MSG="Update configs on branch $BRANCH $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$COMMIT_MSG" || {
  echo "Нет новых изменений для коммита."
  exit 0
}

# Пушим в origin ту же самую ветку, если её ещё нет — создаём удалённую ветку
git push -u origin "$BRANCH"

echo "✅ Успешно задеплоено ветку '$BRANCH': $COMMIT_MSG"
