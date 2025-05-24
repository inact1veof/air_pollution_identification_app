#!/bin/bash
PATH_DATA=/var/lib/postgresql/backup/
data=$PATH_DATA/$BACKUP_FILE
POSTGRES_USER=$DB_USER
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <$data
