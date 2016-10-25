# Automation
Use fabric automation provided by `ep_deploy`. Includes:
- nginx configuration
- install docker (@todo)
- configure AWSLog agent, incl. alarms and metrics
- update git project
- build containers
- manage container life cylce (start/stop)
- `local_settings.py` settings

# Create Superuser
Via `initial_data.json` fixtures.

# Messaging
Exchanges are automatically created given the name in setting `IODICUS_MESSAGING_EXCHANGE_NAME`