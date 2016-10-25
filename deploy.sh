#!/bin/bash

# extract hostname from URI
function extract_docker_ip {
    #@todo simplify as open http://$(docker-machine ip testbest)
    replaced_protocol=$(echo $DOCKER_HOST | sed -e "s/tcp:\/\///g")
    extracted_ip=`echo $replaced_protocol | awk '{ print substr( $0, 0, length($0)-5 ) }'`
}

# create docker env
if [[ -z ${NEW_DOCKER_MACHINE_NAME} ]];
then
    echo "Using default Docker machine"
else
    echo "Creating new Docker machine named '$NEW_DOCKER_MACHINE_NAME'";
    docker-machine create $NEW_DOCKER_MACHINE_NAME --driver virtualbox
    docker-machine env $NEW_DOCKER_MACHINE_NAME
    eval $(docker-machine env $NEW_DOCKER_MACHINE_NAME)
fi

COMPOSE_PROJECT_NAME=ep

if [[ -z $NO_TESTS ]];
then
    tput setaf 6 && echo "Setting DOCKERFILE_SUFFIX to '-jenkins' for unit testing"
    tput setaf 7
    
    export DOCKERFILE_SUFFIX="-jenkins"
fi

# for external volume addition to save files in -- will not disappear with the container when it is deleted
docker volume create --name=influxdb_data
docker volume create --name=pg_data
docker volume create --name=celery_rabbit_data

# prepare config files
docker build -t dschien/fabric deployment/docker-fabric

CONFIG_FILE_NAME=etc/ep.docker-local.cfg
if [[ ! -f $CONFIG_FILE_NAME ]];
then
    echo "Creating local config file $CONFIG_FILE_NAME"
    cp etc/ep-template.cfg $CONFIG_FILE_NAME
fi

docker run -v `pwd`:/ep_site -w /ep_site dschien/fabric fab configuration.setup_env:$CONFIG_FILE_NAME configuration.configure_docker_env
docker run -v `pwd`:/ep_site -w /ep_site dschien/fabric fab configuration.setup_env:$CONFIG_FILE_NAME configuration.configure_local_settings

# store the docker ip address
extract_docker_ip
tput setaf 6 && echo "Retrieved Docker IP of $extracted_ip"

# stop all containers
if [[ ! -z ${DOCKER_REMOVE_ORPHANS} ]]
then
    tput setaf 1 && echo "Stopping docker-compose containers"
    tput setaf 7
    docker-compose down --remove-orphans
fi

# start mock secure server if dockerised
RUN_MOCK_IN_HOST=1
# @if mock secure server is run inside docker further below ...
if [[ ! -z ${RUN_MOCK_IN_HOST} ]];
then
    # use the IP address of the host machine
    TEST_SECURE_SERVER_HOST=${extracted_ip}
else
    tput setaf 1 && echo "Running monitor in Docker"
    tput setaf 7
    # clone monitor testing harness
    IODICUS_MONITOR_DIRECTORY=deployment/iodicus-monitor
    ./deploy-monitor.sh $IODICUS_MONITOR_DIRECTORY

    # start mock secure server, for testing
    ROOT_DIR=`pwd`
    cd $IODICUS_MONITOR_DIRECTORY
    TEST_SECURE_SERVER_HOST= docker-compose -f $ROOT_DIR/test-services.yml up -d mock_secure_server
    cd $ROOT_DIR

    # use the IP address of the docker container
    TEST_SECURE_SERVER_HOST=`docker inspect --format '{{ .NetworkSettings.IPAddress }}' mock_secure_server`
fi

# start all services
tput setaf 6 && echo "Starting common-services services"
tput setaf 7
docker-compose -f common-services.yml up -d

echo "Waiting for db to come up..."
sleep 5s

if [[ ! -z ${RUN_EP_IN_HOST} ]];
then
    tput setaf 6 && echo "The Energy Portal (EP) and core services must be started manually when outside of Docker, please do this now:"
    tput setaf 2 && echo "python manage.py migrate"
    tput setaf 2 && echo "python manage.py loaddata initial_deploy.json"
    tput setaf 2 && echo "python manage.py loaddata dev-local_credentials.json"
    tput setaf 2 && echo "python manage.py collectstatic --noinput"
    tput setaf 2 && echo "python manage.py integration_test"
    tput setaf 2 && echo "python manage.py runserver 0.0.0.0:8000"
    tput setaf 7
else
    tput setaf 6 && echo "Starting core services"
    tput setaf 7
    docker-compose up -d
    sleep 20s
fi

# start test services
if [[ ! -z ${RUN_MOCK_IN_HOST} ]];
then
    # green text
    tput setaf 6 && echo "The Mock Secure Server (mock_secure_server) must be started manually when outside of Docker, please do this now:"

    tput setaf 2 && echo "cd deployment/iodicus-monitor/node_modules/mock_secure_server && npm start && cd -"

    if [[ ! -z ${RUN_SECURE_IMPORTER_IN_HOST} ]];
    then
        tput setaf 2 && echo "python manage.py import_secure_autobahn -r -s test-server"
    else
        tput setaf 2 && echo "SECURE_SERVER_NAME=test-server docker-compose -f secure-services.yml up -d secure_importer"
    fi

    if [[ ! -z ${RUN_EP_IN_HOST} ]];
    then
        ep_host=0.0.0.0
    else
        ep_host=${extracted_ip}
    fi

    tput setaf 2 && echo "cd deployment/iodicus-monitor/node_modules/mock_ebe && EP_AUTHORIZATION_TOKEN=CHANGE_ME EP_API_HOST=$ep_host EP_MESSAGING_HOST=$extracted_ip SOCKET_PORT=3001 npm start && cd -"
    tput setaf 2 && echo "cd deployment/iodicus-monitor && MOCK_SECURE_SERVER_SOCKET_PORT=3000 npm start && cd -"
else
    tput setaf 6 && echo "Starting test services"
    tput setaf 7
    TEST_SECURE_SERVER_HOST=$TEST_SECURE_SERVER_HOST SECURE_SERVER_NAME=test-server docker-compose -f secure-services.yml up -d secure_importer
    TEST_SECURE_SERVER_HOST=$TEST_SECURE_SERVER_HOST docker-compose -f test-services.yml up -d monitor
fi

# start regular importer
if [[ ! -z ${RUN_SECURE_IMPORTER_IN_HOST} ]];
then
    tput setaf 6 && echo "The Secure Importer must be started manually when outside of Docker, please do this now:"
    tput setaf 2 && echo "python manage.py import_secure_autobahn -r -s default"
    tput setaf 7
else
    tput setaf 6 && echo "Starting Secure Importer"
    tput setaf 7
    SECURE_SERVER_NAME=default docker-compose -f secure-services.yml up -d secure_importer
fi

# open the browser
if [[ ! -z ${RUN_EP_IN_HOST} ]];
then
    # Do nothing
    tput setaf 6 && echo "Done"
else
    tput setaf 6 && echo "Opening Energy Aggregator in web browser: http://$extracted_ip:8000"
    tput setaf 7
    open "http://$extracted_ip:8000"
fi
