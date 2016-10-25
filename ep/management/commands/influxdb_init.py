import logging

from django.core.management import BaseCommand
from influxdb import InfluxDBClient
from django.conf import settings

__author__ = 'schien'

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Maintain InfluxDB'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        client = InfluxDBClient(settings.INFLUXDB_HOST, settings.INFLUXDB_PORT, settings.INFLUXDB_USER, settings.INFLUXDB_PASSWORD)
        client.create_database(settings.INFLUX_DB_NAME, if_not_exists=True)
