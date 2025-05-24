#!/bin/sh

PATH_DATA=$BACKUP_PATH
mkdir -p $PATH_DATA
data=$PATH_DATA/eco-$(date +%d-%m-%Y_%H-%M-%S)

if influxd backup -portable -db $DB_NAME $data; then
   echo 'Influx dump created: '$data
else
   echo 'Influx dump failed'
   exit
fi
