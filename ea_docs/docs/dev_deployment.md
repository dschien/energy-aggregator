# Development Deployment

This document outlines the steps required to deploy the Energy Portal for development purposes.

# Overview

Before you begin, make sure you have the requisite software installed:

1. [Python 3.5](#python)
2. [Docker](#docker-toolbox)
3. [virtualenv](#virtual-environments)

You should then clone the project repository to your local machine:
 
```
git clone --recursive git@github.com:dschien/ep_site.git
cd ep_site/
```

There is an automated, *remote* deployment project at [https://github.com/dschien/ep_deploy](https://github.com/dschien/ep_deploy). This is not completely documented, however, so proceed with caution.

# Installation

## Python
This project requires [Python 3.5](https://www.python.org/). You can obtain an installer for your architecture by visiting [this](https://www.python.org/downloads/release/python-351/) page. Installing Python will also install `pip`, a package manager used for python modules and dependencies.

## Docker Toolbox
Get and install [Docker](https://www.docker.com/docker-toolbox). To verify your installation, run Kitematic and start a default container, such as `hello-world-nginx`. If you have time, go through the [first steps](http://docs.docker.com/windows/started/); this can be performed later if necessary.

## Virtual Environments
To manage project dependencies the [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/) tool is used. Install virtualenv by running:

```
pip install virtualenv
```

## Postgres
The web server container requires the `pg_config` application, provided with Postgres. This must be installed prior to creating the containers and added to the `PATH`.

**Linux** users can install Postgres using:

```
sudo apt-get install postgresql-devel # libpq-dev in Ubuntu/Debian
```

**Mac OSX** users can install Postgres using the following command, or by downloading the Postgres [app](http://postgresapp.com/).

```
brew install postgresql
```

**Windows** users must download the software from [here](https://www.postgresql.org/download/) and install it manually.

## Memcached
The web server container also requires the memcached development headers, provided with `libmemcached`. This must be installed prior to creating the containers.

**Linux** users can install it using:

```
sudo apt-get install libmemcached
```

**Mac OSX** users can install it using:

```
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)" < /dev/null 2> /dev/null
brew install libmemcached
```

**Windows** users must download it from [here](http://libmemcached.org/libMemcached.html).

```
```

## Git
The version control system used within this project is [Git](https://git-scm.com/). To install Git, use your package manager or visit the [download](https://git-scm.com/downloads) page.

**Linux** users can install Git using:

```
sudo apt-get install git
```

**Mac OSX** users can install Git using:
 
```
brew install git
```

## PyCharm
The PyCharm IDE is recommended for use with this project. To install PyCharm, visit the [download](https://www.jetbrains.com/pycharm/download/) page.

# Development Environment

## Creating a Virtual Environment

First, a virtual environment is created for dependency management.

```
virtualenv --python=python3 venv_ep
source ~/YOUR_PROJECT_PATH/ep_site/venv_ep/bin/activate
cd depyloyment/docker-web
pip install django
pip install -r requirements/jenkins.txt
cd ../../
```

If you intend to run the Energy Portal outside of Docker, for example for development purposes, you must specify your hostname (`HOSTNAME`) as settings are overridden based upon this value.

```
cp ep_site/settings/components/env/it033887.py ep_site/settings/components/env/HOSTNAME.py
```

Environment variables containing the database credentials are then defined. The created file should contain credentials for **InfluxDB** and **RabbitMQ**.

```
cp etc/docker-env-template etc/docker-env
vim etc/docker-env
```

## Creating Docker Containers

Open Kitematic and click the **Docker CLI** button; this will open a terminal. To ensure the correct environment variables are being used, use the following commands. You may wish to add these to your terminal profile (`.bashrc` or similar) to ensure that they are run each time you open a terminal.

```
export DOCKER_TLS_VERIFY="1"
export DOCKER_HOST="tcp://192.168.99.100:2376"
export DOCKER_CERT_PATH="/YOUR_USER_PATH/.docker/machine/machines/default"
export DOCKER_MACHINE_NAME="default"
```

Configure the settings file by modifying the template found in the project root. You can generate a value for `SECRET_KEY` by clicking [here](http://www.miniwebtool.com/django-secret-key-generator/).

```
cp local_settings.template.py local_settings.py
vim local_settings.py
```

Now, start Docker:

```
docker-machine restart default
```

### Meta Database

The first database used is Postgres. Before creating a container for the database we must first create a volume to mount its files. The following command mounts the folder `/var/lib/postgresql/data` to the Docker private directory, giving it a name (`pg_data`) for future reference. The container will use the lightweight `busybox` image.

```
docker create -v /var/lib/postgresql/data --name pg_data busybox
```

Then, create a container with the name `db` that will listen at port 5432.

```
docker run [-h HOSTNAME] -p 5432:5432 --name db --env-file etc/docker-env -d --volumes-from pg_data postgres:9.4
```

To verify that the container has been created successfully, `docker ps` can be used; the output should be similar to the following:

```
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
1bd0765e4f5a        postgres:9.4        "/docker-entrypoint.s"   6 seconds ago       Up 5 seconds        0.0.0.0:5432->5432/tcp   db
```

### Timeseries Database

A second database, Influx, is used to store timeseries data. Before creating the database a volume must be created.

```
docker create --volume=/data --name influxdb_data busybox
```

The image for this container must be built from the `deployment` directory. This can be done as follows:

```
cd deployment/influx/0.10
docker build -t dschien/influxdb .
```

To create the database run the following command. This uses the `influxdb` image that we just created.

```
cd ../../../
docker run [-h HOSTNAME] -d -p 8083:8083 -p 8086:8086 --env-file=etc/docker-env --name influxdb --volumes-from influxdb_data dschien/influxdb:latest
```

### Message Queue

A message queue, RabbitMQ, is used for communication within the platform. A volume must be created for the message queue:

```
docker create -v /var/lib/rabbitmq --name celery_rabbit_data busybox
```

The container can then be created using the following command:

```
docker run [-h HOSTNAME] -d -P -p 5675:5672 --volumes-from celery_rabbit_data --hostname rabbit --name rabbit rabbitmq:3-management
```

### Memcache

A memcached container is also used, to cache frequent queries. To create the container, use the following command:

```
docker run [-h HOSTNAME] -p 11211:11211 --name memcache -d memcached
```

### Celery

A Celery Worker monitors the message queue and issues update requests to the relevant sites. This is governed by another container, Celery Beat.

The Celery containers require the `web` image to be built; this is found in `./deployments/docker-web` and can be built using the following command. Any requirements are specified in a file (`./deployments/docker-web/requirements/requirements.txt`) and are installed automatically; if these requirements change this file should be updated and the command re-run.

```
docker build -t web ./deployment/docker-web/
```

The worker and the beat container can now be started as follows:

```
docker run [-h HOSTNAME] --name celery_worker -e "C_FORCE_ROOT=true" -p 5555:5555 --env CONTAINER_NAME=celery_worker -d  --link rabbit --link memcache -v `pwd`:/ep_site -w /ep_site web celery -A ep_site worker -l info
docker run -d [-h HOSTNAME] --name celery_beat -e "C_FORCE_ROOT=true" -d  --link rabbit --link memcache --env CONTAINER_NAME=celery_beat -v `pwd`:/ep_site -w /ep_site web celery -A ep_site beat
```

### Web Server

Create a volume for the static files of the web server.

```
docker create -v /static --name web_static_data busybox
```

To configure the web server for use with the database it must be started. To do this, run the following command. This uses the `web` image that was built in the [Celery](#Celery) section.

```
docker run [-h HOSTNAME] --rm -ti -p 8000:8000 -p 8888:8888 -P --volumes-from web_static_data --link db:db -v `pwd`:/ep_site -w /ep_site web python manage.py migrate
```

This opens a shell inside the web server container by binding to ports 8000 and 8888 and mounting the project at `/ep_site`.

This is fairly in-depth and is bracketed by the `docker run command` structure, where `command` here is `python manage.py migrate`. This tells the manage script to setup the DB (See the [Django Documentation](https://docs.djangoproject.com/en/1.8/topics/migrations/)).
It uses plenty of command line switches:

- `--rm` means, that docker should remove the container after it has terminated. Useful, because we will (re-)start this thing often and we don't want old copies floating around.
- `-p 8000:8000 -p 8888:8888` opens and maps the port, so that we can get to it with the browser (not needed at this stage but we will need it soon).
- `--link db` creates a connection between the db and our web container. That means env variables will be created that we can use. You will find that the host is configured via `DB_PORT_5432_TCP_ADDR`. This is set by docker, based on the IP address of the DB container.
- `-v 'pwd':/ep_site` is the project directory, suffixed by a colon and a mount point. This means mount the current working folder (found using `pwd`) as `/ep_site` locally.
- `-w /ep_site` says, change the working directory to `ep_site` (where we have just mounted our project source code).

The output of this command should look similar to the following:

```
C:\Users\Dan\workspaces\python\ep_site> /python/ep_site:/ep_site -w /ep_site web python manage.py migrate
Operations to perform:
  Synchronize unmigrated apps: messages, staticfiles, cookielaw, djcelery, django_extensions, rest_framework
  Apply all migrations: ep, sessions, contenttypes, auth, admin
Synchronizing apps without migrations:
  Creating tables...
    Creating table celery_taskmeta
    Creating table celery_tasksetmeta
    Creating table djcelery_intervalschedule
    Creating table djcelery_crontabschedule
    Creating table djcelery_periodictasks
    Creating table djcelery_periodictask
    Creating table djcelery_workerstate
    Creating table djcelery_taskstate
    Running deferred SQL...
  Installing custom SQL...
Running migrations:
  Rendering model states... DONE
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying ep.0001_initial... OK
  Applying sessions.0001_initial... OK
```

## Create Superuser

The Superuser is the primary account for the Django admin interface and can be used to access the system when you first log in. It can be used to create subsequent users.

While in a non-dockerised environment you would type `python manage.py createsuperuser`, you can find the containerised command below.

```
docker run [-h HOSTNAME] --rm -ti -p 8000:8000 -p 8888:8888 -P --volumes-from web_static_data --link db:db -v `pwd`:/ep_site -w /ep_site web python manage.py createsuperuser
```

## Copy Static Files

```
docker run [-h HOSTNAME] --rm -ti -p 8000:8000 -p 8888:8888 -P --volumes-from web_static_data --link db:db -v `pwd`:/ep_site -w /ep_site web python manage.py collectstatic
```

## Start the Server

Finally, we are ready to launch!

```
docker run [-h HOSTNAME] -d -p 8000:8000 -p 8888:8888 -P --name web --volumes-from web_static_data [--link logstash] --link db:db -v `pwd`:/ep_site -w /ep_site web python manage.py runserver 0.0.0.0:8000
```

You will get back a handle to our container that you can use to interact with the container from the command line. Once again, you can use `docker ps` to verify that the container is running; you should see something like the following:

```
PS C:\Users\Dan\workspaces\python\ep_site> docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
d8a79961cae0        web                 "python manage.py run"   55 seconds ago      Up 55 seconds       0.0.0.0:8000->8000/tcp   web
0000e39710a2        postgres:9.4        "/docker-entrypoint.s"   23 minutes ago      Up 23 minutes       0.0.0.0:5432->5432/tcp   db
```

Note, no container of our `db_data` image is running. That's fine, the volumes are still used by the db container.

## Open the Web Interface.

Once the server container has been started, the web interface can be used. To view the interface we need the IP address of the VM, to obtain this use the following command:

```
docker-machine env
```

This will return something like the following. Note that this will be different depending upon your operating system.

```
PS C:\Users\Dan\workspaces\python\ep_site> docker-machine env --shell=powershell default
$Env:DOCKER_TLS_VERIFY = "1"
$Env:DOCKER_HOST = "tcp://192.168.99.100:2376"
$Env:DOCKER_CERT_PATH = "C:\Users\Dan\.docker\machine\machines\default"
$Env:DOCKER_MACHINE_NAME = "default"
# Run this command to configure your shell:
# C:\Program Files\Docker Toolbox\kitematic\resources\resources\docker-machine.exe env --shell=powershell default | Invoke-Expression
```

The `DOCKER_HOST` is the IP address we need to navigate to. The web server runs at port 8000 and can be seen by browsing to `http://192.168.99.100:8000`.
