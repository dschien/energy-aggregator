import logging

from django.core.management import BaseCommand, CommandError
from ep.models import Site, SiteProperty

__author__ = 'schien'

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Set a site\'s lat & long'

    def add_arguments(self, parser):
        parser.add_argument('site_name')
        parser.add_argument('lat')
        parser.add_argument('long')

    def handle(self, *args, **options):
        try:
            site = Site.objects.get(name=options['site_name'])
        except Site.DoesNotExist:
            raise CommandError('Site "%s" does not exist' % options['site_name'])

        lat, created = SiteProperty.objects.get_or_create(site=site, key='lat')
        long, created = SiteProperty.objects.get_or_create(site=site, key='long')

        lat.value = options['lat']
        long.value = options['long']
        lat.save()
        long.save()
