# TOC
[Development Setup](https://github.com/dschien/ep_site#deployment)

# Quick Start for once Set up

1. Open Kitematic
1. Open PowerShell
1. Change WD to ep_site root on c:
1. Configure Docker - `docker-machine env default --shell powershell  | Invoke-Expression` - check with `docker ps`
1. Run DB container `docker run -p 5432:5432 --name db --env-file etc/env -d --volumes-from pg_data postgres:9.4`
1. Run web-server: `docker run --rm -ti -p 8000:8000 -p 8888:8888 -P --link db:db -v /c/Users/edxps/PycharmProjects/ep_site:/ep_site -w /ep_site web python manage.py runserver --settings=ep_site.dev_settings`
1. Open (e.g. via Kitematic)


# Development Deployment

## Installation
### Docker Toolbox
Get and install (https://www.docker.com/docker-toolbox)
Make sure you can run kitematic and start a container (e.g. the nginx one)

If you have time go through the first steps here (http://docs.docker.com/windows/started/).
Or return to this later.

### Pycharm
The EP is written in python.
You will want to use pycharm.
Get (https://www.jetbrains.com/pycharm/download/)

Obviously this includes getting git.

## Clone the project
Get this project by running `git clone --recursive git@github.com:dschien/ep_site.git`
(the recursive bit is to also fetch submodules).

Do this in a folder underneath your user holder (e.g. C:\Users\you\ep_site on windows)
(I use `C:\Users\Dan\workspaces\python\ep_site`, so you are not surprised if you see this line somewhere below - you need to adjust the path for you).

## Setup Docker

### Build the web image
From kitematic open a shell (I suggest powershell on windows) and go to your ep_site folder.
Then run the following command `docker build -t web .\docker\`

This will build the docker image for the web app (django) for you.
The dependencies are defined in a requirements file that docker copies over, the pip installs.
If later, during development you need more packages, specify them here, then re-run this command and restart your web container.
This might take some time...

### Configure docker shell runtime
`C:\Program Files\Docker Toolbox\docker-machine.exe env --shell=powershell default | Invoke-Expression`
`docker-machine env default --shell powershell  | Invoke-Expression`


### Configure DB connection
You will need to tell Django how to access the DB.
You do this with two things:
1. rename the file `env-template` in `etc/` to just `env` and decide on a password for the DB. It does not matter what you put in here (no spaces please)
2. configure your dev settings by renaming the file `local_settings.template.py` in `ep_site` to just `local_settings.py` and update the `SECRET_KEY` variable
with a key you can generate [here](http://www.miniwebtool.com/django-secret-key-generator/).

### Create a folder `log` in the project directory

### Run a db container
For the DB we use the default postgres image (not images become containers when they are executed).

*Important:* In order to retain the DB state beyond container life cycles we need to also create a db data volume.
For this, run `docker create -v /var/lib/postgresql/data --name pg_data busybox`
This mounts the folder `/var/lib/postgresql/data` (where postgre will place its DB files by default) somewhere in the
docker private area. It will give it a name for future ref (pg_data) and it will use the busybox image (very lightweight).

Now create the DB container itself, run:
`docker run -p 5432:5432 --name db --env-file etc/env -d --volumes-from pg_data postgres:9.4`
This starts a container with name db, opens port 5432, so that you can connect to it, mounts the volumes from our db_data container,
runs this in deamon mode (`-d`), populates the runtime environment with the variables in `etc/env` and uses the offical postgres 9.4 image.
Wow.

If the output in your docker image looks like garbage you can run `clear` to wipe clean.

### Create a data volume container for static files of the web server
`docker create -v /static --name web_static_data busybox`


### Start the web container for configuration
Now we need to prepare our DB for use by django.

For this, we need to interact with django on the shell (through the manage script). That means, we need to start the
web container. We will not yet start the application server.

With docker we get a shell into our container like this (this does not work, yet):
`docker run -ti <container> bash`
This means, run the container and in there the command `bash` but keep the connection open (-ti). Read more about it here:
(http://docs.docker.com/engine/reference/run/)
You can use this if you want to connect to any container. Some don't have bash, then just run the minimal shell (`sh`) instead.

The full command for our web container is slightly more involved:
`docker run --rm -ti -p 8000:8000 -p 8888:8888 -P --volumes-from web_static_data --link db:db -v /c/Users/edxps/PycharmProjects/ep_site:/ep_site -w /ep_site web python manage.py migrate --settings=ep_site.dev_settings`
Uff, let's break this down.
This command is bracketed by the `docker run command` structure from above.
The command here is
`python manage.py migrate --settings=ep_site.dev_settings`
This tells the manage script to setup the DB [Django Docs](https://docs.djangoproject.com/en/1.8/topics/migrations/) and to get the settings from the file ep_site.dev_settings, which we configured above.
It uses plenty of command line switches.
`--rm` means, that docker should remove the container after it has terminated. Useful, because we will (re-)start this thing often and we don't want old copies floating around.
`-p 8000:8000 -p 8888:8888` opens and maps the port, so that we can get to it with the browser (not needed at this stage but we will need it soon).
`--link db` creates a connection between the db and our web container. That means env variables will be created that we can use. See them in action in the file `ep_site.dev_settings`
in the `DATABASES` section. You will find that the host is configured via `DB_PORT_5432_TCP_ADDR`. This is set by docker, based on the IP address of the DB container. Cool...!
`-v /c/Users/edxps/PycharmProjects/ep_site:/ep_site` we have seen above. This time it has a colon. This means mount the folder `/c/Users/edxps/PycharmProjects/ep_site` as /ep_site
 locally. Check out the weird syntax `/c/Users/edxps/PycharmProjects/ep_site` is windows specific. It refers to my local folder `C:\Users\Dan\workspaces\python\ep_site`.
 *So you need to change that to fit your setup.*
`-w /ep_site` says, change the working directory to `ep_site` (where we have just mounted our project source code...).

This should look similar to
```
/python/ep_site:/ep_site -w /ep_site web python manage.py migrate --settings=ep_site.dev_settings
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
PS C:\Users\Dan\workspaces\python\ep_site>
```

If you had wanted, you could have achieve the same if you had ran:
`docker run --rm -ti -p 8000:8000 -p 8888:8888 -P --link db:db -v /c/Users/edxps/PycharmProjects/ep_site:/ep_site -w /ep_site web bash`
and then typed (i mean of course copied)
`python manage.py migrate --settings=ep_site.dev_settings`
*See why?*

#### Install fixtures
Finally, install the fixtures (existing prefect measurements)
`docker run --rm -ti -p 8000:8000 -p 8888:8888 -P --volumes-from web_static_data --link db:db -v /c/Users/edxps/PycharmProjects/ep_site:/ep_site -w /ep_site web python manage.py loaddata ep/fixtures/dump_prefect_data.json --settings=ep_site.dev_settings`
That will take a while.
We expect something like:
```
PS C:\Users\Dan\workspaces\python\ep_site> docker run --rm -ti -p 8000:8000 -p 8888:8888 -P --volumes-from web_static_data --link db:db -v /c/Users/edxps/PycharmProjects/ep_site:/ep_site -w /ep_site web python manage.py loaddata ep/fixtures/dump_prefect_data.json --settings=ep_site.dev_settings
Installed 26867 object(s) from 1 fixture(s)
```

#### Copy static files
Run `docker run --rm -ti -p 8000:8000 -p 8888:8888 -P --volumes-from web_static_data --link db:db -v /c/Users/edxps/PycharmProjects/ep_site:/ep_site -w /ep_site web python manage.py collectstatic --settings=ep_site.dev_settings`

### Create super user
Run `docker run --rm -ti -p 8000:8000 -p 8888:8888 -P --volumes-from web_static_data --link db:db -v /c/Users/edxps/PycharmProjects/ep_site:/ep_site -w /ep_site web python manage.py createsuperuser --settings=ep_site.dev_settings`

#### Start server
Finally, we are ready to launch. Run
`docker run -d -p 8000:8000 -p 8888:8888 -P --name web --volumes-from web_static_data --link logstash --link db:db -v /c/Users/edxps/PycharmProjects/ep_site:/ep_site -w /ep_site web python manage.py runserver --settings=ep_site.dev_settings 0.0.0.0:8000`
You will get back a handle to our container that you can use to interact with the container from the command line.
Run `docker ps` to inspect the running containers.
You should see something like

```
PS C:\Users\Dan\workspaces\python\ep_site> docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
d8a79961cae0        web                 "python manage.py run"   55 seconds ago      Up 55 seconds       0.0.0.0:8000->8000/tcp   web
0000e39710a2        postgres:9.4        "/docker-entrypoint.s"   23 minutes ago      Up 23 minutes       0.0.0.0:5432->5432/tcp   db
```
Note, no container of our `db_data` image is running. That's fine, the volumes are still used by the db container.

#### Open the web interface.
Our web server runs at 8000. However, we need to get the IP of the VM in order to browse to it (on linux you can skip this).
To do this run
`docker-machine env --shell=powershell default`
This will return something like
```
PS C:\Users\Dan\workspaces\python\ep_site> docker-machine env --shell=powershell default
$Env:DOCKER_TLS_VERIFY = "1"
$Env:DOCKER_HOST = "tcp://192.168.99.100:2376"
$Env:DOCKER_CERT_PATH = "C:\Users\Dan\.docker\machine\machines\default"
$Env:DOCKER_MACHINE_NAME = "default"
# Run this command to configure your shell:
# C:\Program Files\Docker Toolbox\kitematic\resources\resources\docker-machine.exe env --shell=powershell default | Invoke-Expression
```
The last line is what you need to setup your command line env to work with docker. Because we opened this through kitematic we don't need
to manually do this.
If you don't like kitematic, you can open a powershell yourself and run the last line literally.

We also see the IP. Copy that and browse to `http://192.168.99.100:8000`. That should open something a web page saying
# No login at the moment.
Then everything is well. Now browse to `http://192.168.99.100:8000/admin` and login with the username of the superuse you
  created before.

You should see a section *ep* with prefect data to browse.

Now go back to `http://192.168.99.100:8000/` and you should see something like:
![Landing after login](http://i.imgur.com/vVb4IDt.png)

# Define pycharm interpreter
With the web container running, open the project settings, define new remote interpreter
select the docker machine, then the web container. Done.

## 101 of Django directory layout
Django uses one directory for central config files - here `ep_site`. 
All other components sit in "apps". These are activated in the `INSTALLED_APPS` directive in the `ep_site.settings` file.
There are plenty of frameworks used. But from our local apps, there is only one: `ep`.

This is where the fun happens.

A project has `admin, models, views, urls, tests` files and `fixtures and templates` directories.
We also add `controllers` and `management`. The rest is JS/HTML/CSS stuff.

If you use [celery](http://www.celeryproject.org/) as we do, then it also has `tasks` (this is where we trigger fetching gateway data). 

### Models 
This is an ORM to create objects from your database rows.

### Admin
Out of the box GUIs for your DB content.

### Views
Here you define what happens if you request an URL.

### URLs
Here you define what urls you want to respond to.

### Fixtures
Here is initial data for your DB

### Templates
These are HTML pages with extra powerups to fill them with dynamic data. 

# First steps

Browse to `http://192.168.99.100:8000/badock/devices` to see a list of devices.
Click on one to get to the details page.

How does this work?
What you see is the contents from templates
 `ep/templates/ep/prefectdevice_list` and `ep/templates/ep/prefect_detail`

Go have a look what is happening here.
Find a description of the django template syntax [here](https://docs.djangoproject.com/en/1.8/topics/templates/).

How do the templates get rendered?

The file `ep/urls/web.py` has a list of patterns. This is being linked to from `ep_site/urls` - the main urls definition.
Among these you just saw `(?P<site>[\w]+)/devices` and `(?P<site>[\w]+)/device/(?P<prefect_id>[0-9]+)/` catching.
If they match your browser url, they will call the View classes `PrefectDeviceDetailView` and `PrefectDeviceListView`.
These also contain keyword args `site` and `prefect_id`. These will be forwarded to the views.

Most interesting is the `PrefectDeviceDetailView`. It specifies a template to render and how to fill the template rendering
context with data.
It does that by retrieving the device data from the models ( defined in `ep/models`).
It then simply adds the object to the context.

It also shows a D3 graph. If you look into the template or inspect via the browser you'll find that it is an API url
where this data comes from.


# API Development ABC

Now look at the other url file `ep/urls/api`.
This also catches patterns `data/(?P<site>[\w]+)/device/(?P<prefect_id>[0-9]+)`
And then calls `get_data` in `apiviews`.
Pro tip: Find out how you can use keyboard shortcuts to navigate from the api urls definition directly to the definition of the view.
(F3 on my layout "Eclipse" - bring up the settings, keymap and search for navigate declaration to find out).

This view returns CSV data under the URL `/api/data/(?P<site>[\w]+)/device/(?P<prefect_id>[0-9]+)`.
This you can use to get a csv of historic data for a device.

For example, if you navigate to `http://192.168.99.100:8000/api/api/data/BADOCK/device/6004` your browser should download
 a cvs with the temp readings for this room.

## Django Restframework

As you can see in the apiview import statement, the above fw is used to render DB models.
```
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAdminUser
```

It is advised to use this for additional APIs.
There is a lots of documentation [here](http://www.django-rest-framework.org/).


## Handling JS Dependencies
It is advised to use bower to manage JS dependencies. 

For that you need grunt and bower. You can run both through ... docker, yay! So cool!

run `docker build -t npmbuilder -f deployment/NPMDockerfile docker` to build the image.
Then run `docker run -v /c/user/<jadajada>/ep_site:/app -w /app/ep -ti npmbuilder bash` to log on.
Or run `docker run -v /c/user/<jadajada>/ep_site:/app -w /app/ep -ti npmbuilder bower install` to install all dependencies 
into the `bower_components` directory.

Aslo run `npm install --dev` to install the grunt dev dependencies. 

Then run 
`docker run -v /c/user/<jadajada>/ep_site:/app -w /app/ep -ti npmbuilder grunt copy` to copy those files to where you can
reference them in your templates - this is the `../static` directory in the project root. 
`Grunt copy` finds this setting defined in the variable `<%= targetdir%>` in the `Gruntfile` in the ep directory.

If you have additional dependencies, you can install these by running `bower install <name>`.
Then add a section to the copy fragment in the Gruntfile. 
It is pretty self evident.
`{dest: "<%= targetdir%>/lib/", src: ["**"], cwd: 'bower_components/jquery/dist/', expand: true},` copies all files from
 `bower_components/jquery/dist/` to the targetdir `lib` folder.
  

# Running Pandas
Pandas is already installed in the container.

Run 
`docker run --rm -ti -p 8888:8888 --link db:db -v /c/Users/edxps/PycharmProjects/ep_site:/ep_site -w /ep_site web sh -c "ipython notebook --ip=* --no-browser"` 

This will run the ipython notebook with port 8888 (default). Don't do this on the cloud server!

You will find there is already a pandas notebook that gets you going in file `plot_temp.ipynb`.

# Importing Prefect device data

You need to rename the file `ep_config.template` in `ep/` to just `ep_config` and insert your prefect API tokens.

Then either use the python shell ...

`docker run --rm -ti -p 8000:8000 -p 8888:8888 -P --link db:db -v /c/Users/edxps/PycharmProjects/ep_site:/ep_site -w /ep_site web python manage.py shell --settings=ep_site.dev_settings`

... or the ipython notebook.

Then run to fetch the content. Adjust `past_days` as desired.
```
from ep.controllers.prefect import PrefectController
from ep.models import PrefectDevice, PrefectDeviceMeasurement
from ep.tasks import collect_prefect
c = PrefectController.for_badock()

past_days = 10

ids = c.get_node_ids()

for node in ids:
    status = c.get_node_status(dev_id)

for dev_id in ids:
    status = c.get_node_status(dev_id)
    device = c.get_device(status)
    for day in range(0,past_days):
        entries = c.get_node_history(dev_id, day)
        m = None
        for entry in entries:            
            m = c.persist_history_entry(entry, device)
    device.most_recent_status = m
```



# Pulling prefect data 
## Rabbit
 `docker run -d --hostname rabbit --name rabbit rabbitmq:3-management`
 
## Celery


# Logging
## elasticsearch and kibana
elastic search persist storage
`docker create -v /usr/share/elasticsearch/data --name elkdata busybox`

Build elasticsearch
`docker build -t elasticsearch -f deployment/docker-elk/elasticsearch/Dockerfile deployment/docker-elk/elasticsearch`

Build kibana
`docker build -t kibana -f deployment/docker-elk/kibana/Dockerfile deployment/docker-elk/kibana`

Run the commands in start_elk.sh
```
docker run --name elasticsearch -d --volumes-from elkdata -p 9200 elasticsearch elasticsearch -Des.network.host=0.0.0.0
docker run -d --link elasticsearch -v $(pwd)/deployment/docker-elk/kibana/config/kibana.yml:/opt/kibana/config/kibana.yml -p 5601 kibana
docker run -d --name logstash -h logstash -p 5000:5000 --link elasticsearch -v $(pwd)/deployment/docker-elk/logstash/config:/etc/logstash/conf.d logstash logstash -f /etc/logstash/conf.d/logstash.conf
```

You can test ELK by running
`echo 'test' | nc -v -w 1 192.168.99.100 5000`

# Jenkins CI

Log in on [dev.iodicus.net] - use github credentials.

Run `docker run -h jenkins --rm -p 8080:8080 --volumes-from web_static_data --link db -v /var/jenkins_home jenkins_django`



## Install plugins
 Cobertura
 Violations
 Git
 
## Specify new project
From git
Add git key from private/passwords

## Config django
Run once, then edit local_settings and add secret key

edit ep.ep_config and add prefect keys

## Create log folder


# Update Docker
`cd /var/lib/jenkins/workspace/EP/deployment/docker-web`
`docker pull dschien/web-bare`
`docker restart db`
`docker build -t web-jenkins -f DockerfileWebJenkins .`


---
This needs updating.
You might find interesting stuff here.
# Old Content

# Deployment
run rabbit in docker
1. create a data vol
`docker create -v /var/lib/rabbitmq --name celery_rabbit_data busybox`

`docker run -d -p 5675:5672 -p 8085:15672 --volumes-from celery_rabbit_data --hostname rabbit --name celery_rabbit rabbitmq:3-management`

RabbitMQ installs with a default username / password of guest / guest
you can change that by creating a new user
```
rabbitmqctl add_user myuser mypassword
rabbitmqctl add_vhost myvhost
rabbitmqctl set_permissions -p myvhost myuser ".*" ".*" ".*"
view raw
```


# Celery
start celery itself with 
`celery -A ep_site worker -l info`

and celery beat with 
`celery -A ep_site beat`

## REPL
Start a worker (e.g. `celery -A ep_site worker -l info`) then:

```
from django.conf import settings
from celery import Celery
app = Celery('ep')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
from ep.tasks import send_msg
send_msg.delay('{msg:"hi"}')
```

That should result in a message to the iodicus messaging system

# DB setup

## Dev Env - OSX
Use postgre app

```
createdb ep
createuser -P ep
```

start db console via icon or on shell
```
psql
```

Then grant user rights:
```
GRANT ALL PRIVILEGES ON DATABASE ep TO ep;
```

Setup the DB
```
./manage.py migrate
```


# Migrations
This is similar to the way things were in south
1. makemigrations
2. migrate 

from the docs:
"If you want to give the migration(s) a meaningful name instead of a generated one, you can use the --name option:"
```
$ python manage.py makemigrations --name changed_my_model your_app_label
```

Always commit the migrations together with the model changes.

# Reset DB
1. reset
`./reset_db.sh`
2. create super user
`python -c 'from ep_site.config_scripts import *; create_su()'`


# Configuration
Rename `local_settings.template` to `local_settings` and set necessary passwords


# Management
# Prefect Type mappings
Use chrome inspector on prefect site `https://pre2000.co.uk/Engineering/{site}}/NodeDetail`
Copy the json response from `/Site/{site}/CompleteNodeInfo` into a file ep/management/data/{site}.json 

Then import those mappings with:
`./manage.py load_prefect_types  badock  /Users/schien/workspaces/python/ep_site/ep/management/data/badock.json`

`./manage.py load_prefect_types  goldney  /Users/schien/workspaces/python/ep_site/ep/management/data/goldney.json`
and 


# Django settings
## following (https://ashokfernandez.wordpress.com/2014/03/11/deploying-a-django-app-to-amazon-aws-with-nginx-gunicorn-git/)
Create a folder where the settings.py of your Django project is located called settings that has four Python files in it
```
init.py
common.py for all your common Django settings
dev.py for your local Django settings
prod.py for your server Django settings
```
At the top of both dev.py and prod.py add the line from <django_project_name>.settings.common import *
Change the
```
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "<django_project_name>.settings")
```

in both wsgi.py and manage.py to
```
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "<django_project_name>.settings.prod")
```
This means that the project with default to the production settings, however you can run it locally using
```
python manage.py runserver --settings=<django_project_name>.settings.dev
```

# PyCharm local run config
DJANGO_SETTINGS_MODULE=ep_site.dev_settings


# Docker

1. run pg with explicit name db

[opt] for extra logging convenience run elk (currently only with compose)
 - link logstash container to web

2. run web with link to db and logstash:elk if using 

attach
a. migrate
b. load fixtures


## Build web image
run `docker build -t web .` to build a local image for django with all dependencies

## Docker compose
run `docker-compose -f docker/dev.yml up` to start the db container

## Run pg-data and pg containers
`docker create -v /var/lib/postgresql/data --name pg_data busybox`

`docker run -p 5432:5432 --name db --env-file etc/env -d --volumes-from pg_data postgres:9.4`

`docker run -ti -p 8000:8000 --name web --env-file etc/env -d --link db web bash`


## Run web

### Start
#### unix
`docker run -ti -p 8000:8000 -P --name web --link db:db -v `pwd`:/ep_site -w /ep_site web bash`
`docker run -d -p 8000:8000 -P --name web --link db:db -v `pwd`:/ep_site -w /ep_site web python manage.py runserver --settings=ep_site.dev_settings 0.0.0.0:8000`

#### Windows
docker stop web
docker rm web
`docker run --rm -p 8000:8000 -P --name web --link db:db -v /c/Users/edxps/PycharmProjects/ep_site:/ep_site -w /ep_site web python manage.py migrate --settings=ep_site.dev_settings`
`docker run --rm -ti -p 8000:8000 -P --name web --link db:db -v /c/Users/edxps/PycharmProjects/ep_site:/ep_site -w /ep_site web python manage.py createsuperuser --settings=ep_site.dev_settings`
`docker run -d -p 8000:8000 -P --name web --link db:db -v /c/Users/edxps/PycharmProjects/ep_site:/ep_site -w /ep_site web python manage.py runserver --settings=ep_site.dev_settings 0.0.0.0:8000`


`python manage.py shell --settings=ep_site.dev_settings`
`from ep.views import *`
``

## Run with ELK
@todo - fix hardcoded container name
`docker run -d -p 8000:8000 -P --name web --link db:db --link dockerelk_logstash_1:elk -v `pwd`:/ep_site -w /ep_site web python manage.py runserver --settings=ep_site.dev_settings 0.0.0.0:8000`

### Load fixtures

`python manage.py loaddata ep/fixtures/dump_prefect_data.json --settings=ep_site.dev_settings`

### log on
`run -ti -p 8000:8000 -P --name web --link db:db -v `pwd`:/ep_site -w /ep_site web bash`


## Logging

We use ELK
Follow this guide:
https://www.digitalocean.com/community/tutorials/how-to-install-elasticsearch-logstash-and-kibana-elk-stack-on-ubuntu-14-04#set-up-filebeat-(add-client-servers)

The git code is in deployment/docker-elk
this is a submodule.
to checkout see here (https://git-scm.com/book/en/v2/Git-Tools-Submodules)
E.g. to fetch submodules run `git clone --recursive ` 
To init submodules late (i.e. after the containing repo was already cloned) use 
`git submodules update --init module_path`

Start a data volume for elk
`docker run -d -v /data --name dataelk busybox`

Celery beat only logs to stderr.
To get that to ELK run a forwarder:
(http://www.sandtable.com/forwarding-docker-logs-to-logstash/)

To create ssl certs for logstash-forwarder
`openssl req -x509 -batch -nodes -newkey rsa:2048 -keyout lumberjack.key -out lumberjack.crt`

@todo - also forward other /var/log output to here


# AWS

# DB docker
`docker run -p 5432:5432 --name db --env-file etc/env -d --volumes-from pg_data postgres:9.4`

# Web docker

`docker run -ti -h ep -p 8000:8000 -p 8888:8888 -P --link db:db -v `pwd`:/ep_site -w / --entrypoint bin/bash dschien/web`

## Install Jenkins CI
https://blogs.aws.amazon.com/application-management/post/Tx32RHFZHXY6ME1/Set-up-a-build-pipeline-with-Jenkins-and-Amazon-ECS

### Behind SSL
https://www.digitalocean.com/community/tutorials/how-to-configure-nginx-with-ssl-as-a-reverse-proxy-for-jenkins
jenkins conf is in /etc/sysconf/jenkins

Open security group ports for github hooks:
(https://help.github.com/articles/what-ip-addresses-does-github-use-that-i-should-whitelist/)

Update rootCA according to:
(https://help.github.com/enterprise/11.10.340/admin/articles/using-self-signed-ssl-certificates/)
(http://kb.kerio.com/product/kerio-connect/server-configuration/ssl-certificates/adding-trusted-root-certificates-to-the-server-1605.html)

Make sure you update the nginx.conf

@todo
Embed concrete config file snippets

### Webhook
- install jenkins github plugins
- Enable webhooks in jenkins
- Create webhook in github (https://github.com/dschien/ep_site).
- url is (https://dev.iodicus.net/github-webhook/)
- trailing slash is crucial
- Set payload type to json
- with self-signed certs, disable ssl verification


## EP itself
### Load Balancer
#### Self-signed keys
(https://support.eucalyptus.com/hc/en-us/articles/202440330-Steps-to-Create-HTTPS-SSL-Elastic-Load-Balancer-on-Eucalyptus)


# Jenkins Build container


 In `/var/lib/jenkins/workspace/EP/deployment/docker-web`
 run 
 `docker build -t web-jenkins -f DockerfileWebJenkins .`


# ELK
## Logstash
Config files are in `/etc/logstash/conf.d/`
e.g. `02-filebeat-input.conf`


# Settings

- local settings are not in VCS and contains secrets
- prod settings are for prod
- dev settings are for dev
- jenkings settings are for test
- settings are common

# Messaging system

# Description
We are using a fanout exchange (See Description  [here](https://www.rabbitmq.com/tutorials/amqp-concepts.html) and [here](http://www.rabbitmq.com/tutorials/tutorial-three-python.html))
which means the exchange broadcasts to all registered queues.

Subscribers register a queue and bind it to the exchange. Messages that were received before the queue was connected will 
be lost.

We are persisting messages. In order to guard against exchange overflow we can set message TTL on the queues.
This can be done by consumers when declaring their queues, or as a system wide settings via a policy:
`rabbitmqctl set_policy TTL ".*" '{"message-ttl":1800000}' --apply-to queues`
In this example a TTL of 1800s = 30 minutes is set

Connect downstream from the EP
Via rabbit
`docker run -d -p 5671-5672:5671-5672 -p 8080:15672 -v ~/tmp/rabbit_data:/var/lib/rabbitmq --hostname messaging --name messaging-rabbit rabbitmq:3-management`

`docker run -ti --env-file etc/env -v `pwd`/deployment/rabbitmq-config/ssl:/ssl -v `pwd`/deployment/rabbitmq-config/config:/etc/rabbitmq -p 5671-5672:5671-5672 -p 8080:15672 -v ~/tmp/rabbit_data:/var/lib/rabbitmq --hostname messaging.iodicus.net --name messaging-rabbit rabbitmq:3-management bash`


# API Design

## Secure
Secure bundles are info per gateway as
```
 gateway_response = [
    zone_1: [
        {devices: [
            {dev_id: 123,
            dev_params: [
                dev_param_id:123,
                dev_param_type: abc,
                dev_param_value: 0,
            ]}
        ]}
    ]
 ]
```

While Prefect just knows

```
node : {
    current_temp,
    etc
}
```

The current is a superset of both it consist of a type
Node with a set of Devices with each having a set of DeviceParameters for which there are Measurements and Events.

A node is a bundle of more than one device. This is largely equivalent to a room, except in BMS terminology, but more than 
one room can be part of a space.  

Querying measurements thus looks like this:
1. get a device id by browsing for nodes and then devices
e.g node room 6001 > device temperature_control
2. get a list of device parameters
temperature_control > current_temperature
                    > setpoint_temperature


`/api/device_parameter_id`


We started from to get temperature measurements
`/api/site/<site_id>/node/<node_id>`

The natural evolution for multiple criteria would be
`/api/site/<site_id>/node/<node_id>/parameter`

However, in order to be able to represent both the Prefect as well as the Secure structure, we chose to adopt a superset. 
 That means, we have somewhat anemic models in the case of pre 
 
 
