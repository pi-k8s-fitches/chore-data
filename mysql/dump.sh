#!/usr/bin/env sh

apk add mariadb-client

until nc -zw3 mysql 3306; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

mysql/load.py

echo "All services up"

mysqldump -h mysql -u root -B nandy > mysql/nandy.sql