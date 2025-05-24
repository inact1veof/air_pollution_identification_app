# syntax=docker/dockerfile:1
FROM postgres:12
WORKDIR /var/lib/postgresql/data/pgdata
COPY .pgpass /var/lib/postgres/
COPY dump_data.sh /var/lib/postgresql/scripts/
COPY restore_data.sh /var/lib/postgresql/scripts/
COPY backup/ /var/lib/postgresql/backup_init/
COPY init_db.sh /docker-entrypoint-initdb.d
COPY restore_data_init.sh /docker-entrypoint-initdb.d

RUN  chmod 600 /var/lib/postgres/.pgpass \
     && chmod a+x /var/lib/postgresql/scripts/*.sh \
     && chmod a+x /docker-entrypoint-initdb.d/*.sh \
     && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8

COPY postgresql.conf /etc/postgresql/
COPY pg_hba.conf /etc/postgresql/
COPY pg_ident.conf /etc/postgresql/

# Expose the PostgreSQL port
EXPOSE 5432

# Add VOLUMEs to allow backup of config, logs and databases
VOLUME  ["/var/log/postgresql", "/var/lib/postgresql/data","/var/lib/postgresql/scripts"]