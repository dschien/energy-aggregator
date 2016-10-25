import asyncio
import logging
import time
from django.conf import settings

from django.core.management import BaseCommand

from ep.models import Node
from ep_rayleigh_importer.controllers.rayleigh_client import RayleighClient

__author__ = 'mitchell'

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import now'

    def handle(self, *args, **options):
        logger.info("Starting importer for host: " + settings.RAYLEIGH_HOST)
        self.client = RayleighClient(
            settings.RAYLEIGH_CLIENT_ID,
            settings.RAYLEIGH_TOKEN,
            settings.RAYLEIGH_APP_ID,
            settings.RAYLEIGH_HOST
        )

        self.last_checked_time = self.ms_from_unix_epoch()

        loop = asyncio.get_event_loop()
        self.tasks = [
            asyncio.ensure_future(self.device_importer()),
            asyncio.ensure_future(self.sensor_importer())
        ]

        try:
            logger.debug("Starting event loop")
            loop.run_until_complete(asyncio.wait(self.tasks))
        except KeyboardInterrupt:
            pass

    DEVICE_IMPORT_FREQUENCY = 60 * 60
    SENSOR_IMPORT_FREQUENCY = 60 * 5

    last_checked_time = None

    @staticmethod
    def ms_from_unix_epoch():
        return str(int(round(time.time() * 1000)))

    def get_devices(self):
        return Node.objects.filter(gateway=self.client.rayleigh_gw)

    async def device_importer(self):
        while True:
            logger.info('Checking Rayleigh for new devices')
            self.client.retrieve_devices()
            await asyncio.sleep(self.DEVICE_IMPORT_FREQUENCY)

    async def sensor_importer(self):
        while True:
            now = self.ms_from_unix_epoch()
            logger.info('Checking Rayleigh for sensor readings')
            devices = self.get_devices()

            for device in devices:
                logger.info('Retrieving sensors from device {}'.format(device))
                sensors = self.client.retrieve_sensors(device)

                self.client.retrieve_sensor_readings(device, sensors, self.last_checked_time, now)
            self.last_checked_time = now
            await asyncio.sleep(self.SENSOR_IMPORT_FREQUENCY)
