import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

import ep.models

logger = logging.getLogger(__name__)


# @todo review this
# This code is triggered whenever a new user has been created and saved to the database
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    logger.info("Creating auth token for user %s" % instance.username)
    if created:
        if not Token.objects.filter(user=instance).exists():
            Token.objects.create(user=instance)
        else:
            print('Token exists, skipping generation')
