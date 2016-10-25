## Config file templating
 The EP uses the django settings file mechanism for configuration.
  
 When `deploy.sh` is run `ep-template.cfg` will be copied to the config file name in variable `CONFIG_FILE_NAME` env var.
 The default is `ep.docker-local.cfg`. If the named file exists, it will not be overriden.
 
 The config file values in these files will be used to generate the `local_settings.py` file which is read at run-time.
 
 Do not check in `.cfg` files into source control. Do not enter your configuration settings into the template.
 
 - Run `deploy.sh` once to generate your config file.
 - Make desired changes to  `ep.docker-local.cfg` or whatever config file you want to use.
 - Run `deploy.sh` again