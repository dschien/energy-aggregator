# Energy Portal Testing

This document describes how to perform end-to-end testing of the Energy Portal using the [Monitor](https://github.com/lukem512/iodicus-monitor) testing harness.

## Setting up the testing environment

1. Postgres, Influx, Memcached, RabbitMQ, Celery Beat and Celery Worker containers need to be running, as per the [dev_deployment](dev_deployment.md) document. These must be named containers to allow the links in the commands in this document to work correctly.

2. The Mock Secure Server container needs to be running. If you need to create this image, the following command can be used:

```
git clone https://github.com/lukem512/iodicus-monitor.git
cd iodicus-monitor/
docker build -t lukem512/iodicus-monitor .
```

To run the container, the following command is used:

```
docker run [-h HOSTNAME] --rm -ti --name mock_secure_server --entrypoint /mock_secure_server_entrypoint.sh --link celery_worker --name mock_secure_server lukem512/iodicus-monitor
```

3. The Energy Aggregator (web server) container needs to be running. This may already be running - in which case skip this step.

```
docker run [-h HOSTNAME] --rm -ti -p 8000:8000 -p 8888:8888 -P --volumes-from web_static_data --link db:db --link rabbit -v `pwd`:/ep_site -w /ep_site --name aggregator web python manage.py runserver 0.0.0.0:8000
```

4. The importer for the Mock Secure Server needs to be running.

```
docker run [-h HOSTNAME] --rm -ti  -P --volumes-from web_static_data --link mock_secure_server --link db:db --link rabbit -v `pwd`:/ep_site -w /ep_site --name importer web python manage.py import_secure_autobahn -s test-server -r
```

5. The Monitor container, which also contains a Mock Energy Balancing Engine, can be run to complete the test.

```
docker run [-h HOSTNAME] --rm -ti -e "DEVICE_PARAMETER_ID=1" -e "TARGET_VALUE=123" -e "EP_MESSAGING_HOST=192.168.99.100" -e "EP_MESSAGING_PORT=5675" -e "EP_AUTHORIZATION_TOKEN=YOUR_TOKEN_HERE" -e "EP_API_HOST=aggregator" -e "MOCK_SECURE_SERVER_HOST=mock_secure_secure" -e "MOCK_SECURE_SERVER_SOCKET_PORT=3000" --link aggregator --link mock_secure_server --name monitor lukem512/iodicus-monitor
```

## Running the test

To perform the test, simply modify the value passed to `TARGET_VALUE` so that it will result in a change of the test device state. The Monitor container is then re-launched and, after a timeout (customisable using the `TEST_WAIT_TIME` environment variable), the results are displayed in the terminal.

## Troubleshooting

### Mock EBE cannot connect to Message Queue

If the message is `ECONNREFUSED` then the hostname is set incorrectly. Check that your IP address is `192.168.99.100` by running:

```
docker-machine env
```

If the error message is `Error 404` then it is likely that the exchange name is invalid. This can be set by adding an additional switch to the command when running the Monitor container, such as `-e "EP_MESSAGING_EXCHANGE_NAME=LES_EVENTS"`.

Further diagnostics can be performed by running:

```
docker logs rabbit
```