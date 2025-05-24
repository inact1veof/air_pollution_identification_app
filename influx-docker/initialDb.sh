#!/bin/sh
#file:initialDb.sh
#company:eco_ai
#author:DVorobiev
INFLUXDB_DATABASE_NAME=$DOCKER_INFLUXDB_INIT_BUCKET
INFLUXDB_USER_NAME=$DOCKER_INFLUXDB_INIT_USERNAME
INFLUXDB_USER_PWD=$DOCKER_INFLUXDB_INIT_PASSWORD
# Создать базу данных
echo "Create database: $DOCKER_INFLUXDB_INIT_BUCKET"
influx -execute "create database $DOCKER_INFLUXDB_INIT_BUCKET"
influx -execute "use $DOCKER_INFLUXDB_INIT_BUCKET"
# Создать пользователя и авторизоваться
echo "Create user: $INFLUXDB_USER_NAME and authorization"
influx -execute "create user $INFLUXDB_USER_NAME with password '$INFLUXDB_USER_PWD'"
influx -execute "grant all on $INFLUXDB_DATABASE_NAME to $INFLUXDB_USER_NAME"
# Запросить список пользователей
echo "List users"
influx -execute "use $INFLUXDB_DATABASE_NAME" -execute  "show users"