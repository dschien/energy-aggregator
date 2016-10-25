#!/usr/bin/env bash

# parse command-line argument
# i.e. deploy-monitor.sh monitor_directory
DEFAULT_IODICUS_MONITOR_DIRECTORY=deployment/iodicus-monitor
IODICUS_MONITOR_DIRECTORY=${1:-$DEFAULT_IODICUS_MONITOR_DIRECTORY}
echo "Using IODICUS_MONITOR_DIRECTORY = $IODICUS_MONITOR_DIRECTORY"

echo "Fetching monitor, mock_ebe and mock_secure_server modules using NPM"
if [ -d $IODICUS_MONITOR_DIRECTORY ];
then
    git -C $IODICUS_MONITOR_DIRECTORY pull
else
    git clone https://github.com/lukem512/iodicus-monitor.git $IODICUS_MONITOR_DIRECTORY
fi

# perform NPM install inside docker
docker run -v $(pwd)/$IODICUS_MONITOR_DIRECTORY:/usr/src/monitor -w /usr/src/monitor lukem512/iodicus-monitor npm install
