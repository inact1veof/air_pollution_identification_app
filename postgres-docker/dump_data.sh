#!/bin/bash
set -e  # Остановить выполнение скрипта при критической ошибке
PGUSER=$DB_USER
PGPASSWORD=$DB_PASSWORD
PGHOST=$DB_HOST
PGDATABASE=$DB_NAME

BACKUP_PATH="../backup"
FULL_DUMP_FILE="$BACKUP_PATH/full_db_dump.sql"
ARCHIVE_FILE_FULL_DUMP="$FULL_DUMP_FILE.gz"

echo "Начало полного резервного копирования базы данных $PGDATABASE с сервера $PGUSER@$PGHOST..."
if ! pg_dump -U "$PGUSER" -h "$PGHOST" --format=p --create --clean --file="$FULL_DUMP_FILE" "$PGDATABASE"; then
    echo "Сбой резервного копирования базы данных" >&2
    exit 1
fi
if gzip -c "$FULL_DUMP_FILE" > "$ARCHIVE_FILE_FULL_DUMP"; then
    echo "Полная резервная копия базы данных успешно создана и сжата: $ARCHIVE_FILE_FULL_DUMP"
    rm "$FULL_DUMP_FILE"
else
    echo "Ошибка при сжатии резервной копии" >&2
    exit 1
fi
