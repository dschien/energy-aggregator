# How can I test if the messaging system is reachable?

1. Start a container
`docker-compose run web bash`
2. Open a django shell
`python manage.py shell`
3. Send a message 
```
import json
from celery import current_app
from django.conf import settings
from ep.tasks import send_msg
current_app.conf.CELERY_ALWAYS_EAGER = True
settings.CELERY_ALWAYS_EAGER = True
json.dumps({'test': 1})
```