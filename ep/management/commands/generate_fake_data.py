import logging

from django.core.management import BaseCommand

from ep.tests.test_api_generic import SiteFactory

__author__ = 'schien'

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import now'

    def add_arguments(self, parser):
        parser.add_argument('site_name')

    def handle(self, *args, **options):
        SiteFactory.create(name=options['site_name'])
