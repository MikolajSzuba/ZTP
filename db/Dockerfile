FROM postgres:16

ENV POSTGRES_DB=appdb
ENV POSTGRES_USER=appuser
ENV POSTGRES_PASSWORD=apppassword

COPY ./init/ /docker-entrypoint-initdb.d/

EXPOSE 5432
