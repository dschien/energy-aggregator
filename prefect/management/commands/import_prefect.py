import datetime
import logging
from decimal import Decimal

import pytz
import requests
from django.conf import settings
from django.core.management import BaseCommand
from influxdb import InfluxDBClient

from ep.models import Device, DPMeasurements

from prefect.models import PrefectDeviceParameterType
from prefect.controllers.prefect import PrefectController, badock_site_name

__author__ = 'schien'

logger = logging.getLogger(__name__)
ep_model_logger = logging.getLogger('ep.models').setLevel("WARN")


class Command(BaseCommand):
    """
    Import measurements from prefect sites.
    For example:
    `python manage.py import_prefect <site name>` to import today's readings
    """
    help = 'Import now'

    def add_arguments(self, parser):
        parser.add_argument('site')
        parser.add_argument('-d', '--days-ago', dest='days_ago', default=-1,
                            help='How many days back to import')
        parser.add_argument('-n', '--node-id', dest='node_id', default=0,
                            help='Prefect specific node id to import for. Imports all nodes if not set')

    def handle(self, *args, **options):
        site = options['site']
        options_days_ago_ = int(options['days_ago'])
        if options_days_ago_ == -1:
            logger.info("Importing current values")
            c = PrefectController.by_site_name(site)
            logger.debug('Importing from site: {}'.format(c.site))

            c.update(options['node_id'] if 'node_id' in options else None)
        else:
            logger.info("Importing historic values")
            if site.lower() == badock_site_name:
                headers = {'Authorization': 'Bearer %s' % settings.PREFECT_API_TOKEN_BADOCK}
            else:
                headers = {'Authorization': 'Bearer %s' % settings.settings.components.PREFECT_API_TOKEN_GOLDNEY}

            options_node_id_ = int(options['node_id'])
            if options_node_id_ != 0:
                ids = [options_node_id_]
            else:
                logger.info("Requesting node addresses.")
                url = 'https://pre2000.co.uk/apiv1/SiteApi/{site}/NodeAddresses'.format(site=site.upper())
                r = requests.get(url, headers=headers)
                ids = r.json()

            myclient = InfluxDBClient(settings.INFLUXDB_HOST, settings.INFLUXDB_PORT, settings.INFLUXDB_USER,
                                      settings.INFLUXDB_PASSWORD, settings.INFLUX_DB_NAME)

            for id in ids:
                logger.info("Importing for device {}".format(id))
                for day in reversed(range(options_days_ago_)):
                    logger.info("Importing day {}".format(day))
                    __dp = None
                    try:
                        url = 'https://pre2000.co.uk/apiv1/SiteApi/{site}/NodeHistory/{daysAgo}/{id}'.format(
                            site=site.upper(), daysAgo=day, id=id)
                        r = requests.get(url, headers=headers)
                        res = r.json()
                        series = []
                        for hist_entry in res[0]['History']:
                            """
                            {'CurrentTemperature': 21.4,
                             'L1On': False,
                             'L2On': False,
                             'ProgramName': '',
                             'ReceivedAt': 1451605892,
                             'SetPointTemperature': -100.0}
                            """
                            node_devices = Device.objects.filter(node__gateway__site__name=site, node__external_id=id)
                            if options['verbosity'] > 1:
                                logger.info("Importing for node {}".format(id))
                            for device in node_devices:
                                epoch = hist_entry['ReceivedAt']
                                localized_receive_time = pytz.utc.localize(datetime.datetime.utcfromtimestamp(epoch))
                                measurement_time = localized_receive_time

                                for device_parameter in device.parameters.all():
                                    __dp = device_parameter.id
                                    if options['verbosity'] > 1:
                                        logger.info(
                                            "Importing for device parameter {}, type {}".format(device_parameter.id,
                                                                                                device_parameter.type.code))

                                    if device_parameter.type.code == PrefectDeviceParameterType.SETPOINT_TEMP:
                                        value = Decimal(str(hist_entry['SetPointTemperature']))
                                    if device_parameter.type.code == PrefectDeviceParameterType.CURRENT_TEMP:
                                        value = Decimal(str(hist_entry['CurrentTemperature']))
                                    if device_parameter.type.code == PrefectDeviceParameterType.RELAY_ONE:
                                        value = Decimal(bool(hist_entry['L1On']))
                                    if device_parameter.type.code == PrefectDeviceParameterType.RELAY_TWO:
                                        value = Decimal(bool(hist_entry['L2On']))
                                    if device_parameter.type.code == PrefectDeviceParameterType.PIR:
                                        # not currently in the API
                                        # value = Decimal(bool(hist_entry['PresenceIsDetected']))
                                        pass
                                    if options['verbosity'] > 1:
                                        logger.info("Storing {time} {value}".format(time=measurement_time, value=value))

                                    point_values = {
                                        "time": measurement_time,
                                        "measurement": DPMeasurements.INFLUX_MEASUREMENT_NAME,
                                        'fields': {
                                            'value': value,
                                        },
                                        'tags': {
                                            DPMeasurements.DP_TAG: int(device_parameter.id),
                                        },
                                    }
                                    series.append(point_values)

                        myclient.write_points(series)

                    except Exception as e:
                        print("exception during node {}, device param {}, day".format(id, __dp, day))
                        print(e)
