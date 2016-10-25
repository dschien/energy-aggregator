import os

import django

from ep.ep_config import superuser_pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ep_site.settings")
django.setup()

__author__ = 'schien'


# from django.conf import settings

# settings.configure(DEBUG=True)


def create_su():
    from django.contrib.auth.models import User

    u = User(username='user')
    u.email = 'CHANGE_ME@gmail.com'
    u.set_password(superuser_pass)
    u.is_superuser = True
    u.is_staff = True
    u.save()
