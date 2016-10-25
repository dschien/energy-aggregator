# Docker Compose

To get the containers running quickly you can use:

`docker volume create --name=pg_data`
`docker volume create --name=celery_rabbit_data`
`docker volume create --name=influxdb_data`
`docker-compose up`

Followed by the usual commands to setup django
 ``