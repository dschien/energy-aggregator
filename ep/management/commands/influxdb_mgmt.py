import logging
from datetime import timezone
from decimal import Decimal

from django.core.management import BaseCommand
from django.utils import dateparse
from influxdb import InfluxDBClient

from ep.models import DPMeasurements
from django.conf import settings

__author__ = 'schien'

logger = logging.getLogger(__name__)


class Row(object):
    def __init__(self, row):
        self.id = row[0]
        self.time = row[1]
        self.value = row[2]
        self.device_parameter_id = row[3]


class Command(BaseCommand):
    help = 'Maintain InfluxDB'

    def add_arguments(self, parser):
        parser.add_argument('-b', '--batch-size', dest='batch', default=10000,
                            help='Number of measurements to write in a single transaction')
        parser.add_argument('-s', '--start-row', dest='start', default=1,
                            help='Row to start')
        parser.add_argument('-f', '--final-row', dest='final', default=-1,
                            help='Row to start')
        parser.add_argument('file')

    def handle(self, *args, **options):
        try:
            series = []

            myclient = InfluxDBClient(settings.INFLUXDB_HOST, settings.INFLUXDB_PORT, settings.INFLUXDB_USER,
                                      settings.INFLUXDB_PASSWORD, settings.INFLUX_DB_NAME)
            print("writing to %s" % myclient._get_host())
            with open(options['file']) as f:
                for i, line in enumerate(f):
                    "['id', 'measurement_time', 'value', 'device_parameter_id']"
                    row = line.strip().split(',')
                    # print(row)

                    if i < int(options['start']):
                        continue
                    if i == int(options['final']):
                        break
                    dt = dateparse.parse_datetime(row[1])

                    point_values = {
                        "time": dt.replace(tzinfo=timezone.utc).isoformat(),
                        "measurement": DPMeasurements.INFLUX_MEASUREMENT_NAME,
                        'fields': {
                            'value': Decimal(row[2]),
                        },
                        'tags': {
                            DPMeasurements.DP_TAG: int(row[3]),
                        },
                    }
                    series.append(point_values)

                    batch_size = int(options['batch'])
                    if i % batch_size == 0:
                        print('writing batch {}'.format(i / batch_size))
                        if options['verbosity'] > 1:
                            print(series)
                        myclient.write_points(series)
                        series = []
                if series:
                    # write final batch
                    print('writing batch {}'.format(i / batch_size))
                    myclient.write_points(series)

        except Exception as e:
            print(e)
            raise e

    def by_sql(self):
        """
            import existing data to influxdb
            """
        import psycopg2
        # Try to connect
        try:
            conn = psycopg2.connect(
                "dbname='ep' user='ep' host='{}' password='{}'".format(settings.DB_HOST, settings.DB_PASSWORD))
        except:
            print("I am unable to connect to the database.")
        cur = conn.cursor('server-cursor')  # server side cursor
        cur.itersize = 1000  # how much records to buffer on a client
        try:

            myclient = InfluxDBClient(settings.INFLUXDB_HOST, settings.INFLUXDB_PORT, settings.INFLUXDB_USER,
                                      settings.INFLUXDB_PASSWORD, settings.INFLUX_DB_NAME)
            cur.execute("""SELECT * from ep_devicestatemeasurement""")

            series = []
            idx = 0
            print('starting copying')
            for row in cur:

                idx += 1
                old = Row(row)
                # MySeriesHelper(device_parameter=old.device_parameter_id, value=old.value, time=old.time)

                pointValues = {
                    "time": old.time,
                    "measurement": DPMeasurements.INFLUX_MEASUREMENT_NAME,
                    'fields': {
                        'value': old.value,
                    },
                    'tags': {
                        DPMeasurements.DP_TAG: old.device_parameter_id,
                    },
                }
                series.append(pointValues)

                if idx % 1000 == 0:
                    print('writing batch {}'.format(idx / 1000))
                    myclient.write_points(series)
                    series = []

            myclient.write_points(series)
            # To manually submit data points which are not yet written, call commit:
            # MySeriesHelper.commit()
        except Exception as e:
            print(e)
