#!/bin/bash
PATH_DATA=/var/lib/postgresql/backup/
data=$PATH_DATA/$1
POSTGRES_USER=$DB_USER
POSTGRES_DB=eco
echo "Restore dump "$data
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <$data
