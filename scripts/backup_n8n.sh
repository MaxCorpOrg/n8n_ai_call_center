#!/bin/bash
# backup_n8n.sh — создаёт бэкап Docker-тома n8n_data

# Переменные
VOLUME_NAME="n8n_data"            # имя Docker-тома, как в вашем docker-compose.yml
BACKUP_DIR="/root/n8n-backups"    # куда сохранять архивы на хосте
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
RETENTION_DAYS=7

# Создать папку для бэкапов
mkdir -p "$BACKUP_DIR"

# Запустить временный контейнер, замапить том и сделать архив
docker run --rm \
  -v "${VOLUME_NAME}":/data:ro \
  -v "${BACKUP_DIR}":/backup \
  busybox \
  sh -c "tar czf /backup/n8n-backup_${TIMESTAMP}.tar.gz -C /data ."

# Проверка успешности
if [ $? -ne 0 ]; then
  echo "[$(date)] ERROR: Не удалось создать бэкап тома ${VOLUME_NAME}" >> "${BACKUP_DIR}/backup.log"
  exit 1
fi

# Удалить старые бэкапы
find "$BACKUP_DIR" -type f -name "n8n-backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Логирование успеха
echo "[$(date)] Backup completed: n8n-backup_${TIMESTAMP}.tar.gz" >> "${BACKUP_DIR}/backup.log"
