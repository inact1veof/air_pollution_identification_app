# syntax=docker/dockerfile:1
FROM influxdb:1.8-alpine
WORKDIR /
ENV DOCKER_INFLUXDB_INIT_MODE=setup
ENV DOCKER_INFLUXDB_INIT_USERNAME=admin
ENV DOCKER_INFLUXDB_INIT_PASSWORD=admin
ENV INFLUXDB_ADMIN_USER=admin
ENV INFLUXDB_ADMIN_PASSWORD=admin

ENV DOCKER_INFLUXDB_INIT_ORG=home
ENV DOCKER_INFLUXDB_INIT_BUCKET=eco
ENV DOCKER_INFLUXDB_INIT_MODE=setup
ENV DB_NAME=$DOCKER_INFLUXDB_INIT_BUCKET
ENV RP_NAME=eco_ai
ENV USERNAME=eco_user
ENV WORD=eco_user
ENV BACKUP_PATH=backup

COPY influxdb.conf /etc/influxdb/influxdb.conf
COPY initialDb.sh /docker-entrypoint-initdb.d/
COPY entrypoint.sh /docker-entrypoint-initdb.d/
COPY initialDb.sh /init-influxdb.sh
COPY backup_influxdb.sh .
RUN mkdir -p backup \
    && chmod a+x /docker-entrypoint-initdb.d/*.sh \
    && chmod a+x /*.sh

EXPOSE 8086

ENTRYPOINT ["influxd"]
CMD ["run", "-config", "/etc/influxdb/influxdb.conf", "-pidfile", "/etc/influxdb/influxd.pid"]