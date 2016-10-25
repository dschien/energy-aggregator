# Energy Aggregator
---
Documentation now in folder ea_docs
---
Current as of 20.07.2016

# Development Deployment

## Clone the project
Get this project by running `git clone --recursive git@github.com:dschien/energy-aggregator.git`
(the recursive bit is to also fetch submodules).

Obviously this includes getting git.

## Docker Toolbox (if not already installed)
Get and install (https://www.docker.com/docker-toolbox)
Make sure you can run kitematic and start a container (e.g. the nginx one)

Potentially set your DOCKER_HOST in environment variables according to Docker documentation.

## Run `deploy.sh`
---

# Configuration

## Config file templating
 The EP uses the django settings file mechanism for configuration.

 When `deploy.sh` is run `ep-template.cfg` will be copied to the config file name in variable `CONFIG_FILE_NAME` env var.
 The default is `ep.docker-local.cfg`. If the named file exists, it will not be overriden.

 The config file values in these files will be used to generate the `local_settings.py` file which is read at run-time.

 Do not check in `.cfg` files into source control. Do not enter your configuration settings into the template.

 - Run `deploy.sh` once to generate your config file.
 - Make desired changes to  `ep.docker-local.cfg` or whatever config file you want to use.
 - Run `deploy.sh` again
---
