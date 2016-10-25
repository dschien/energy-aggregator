import logging

from django.conf import settings
from django.core.management import BaseCommand
import simplejson as json

from ep import tasks
from django.conf import settings
__author__ = 'schien'

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print(settings.IODICUS_MESSAGING_HOST)
        tasks.send_msg.delay(json.dumps("test"))
        # print(settings.BROKER_URL)
        # tasks.health_log_task.delay()
