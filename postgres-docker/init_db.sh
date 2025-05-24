#!/usr/bin/env sh
set -e
psql -v ON_ERROR_STOP=1 --username "$DB_USER"<<-EOSQL
  CREATE DATABASE eco;
  \c eco;
  CREATE EXTENSION pgcrypto;

EOSQL