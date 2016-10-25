import decimal
from split_settings.tools import optional, include
import os
import socket

decimal.getcontext().traps[decimal.FloatOperation] = True

# Must bypass this block if another settings module was specified.
if os.environ['DJANGO_SETTINGS_MODULE'] == 'ep_site.settings':

    local_dev_config = optional('components/env/empty.py')

    if ('RUN_EP_IN_HOST' in os.environ) or ('RUN_SECURE_IMPORTER_IN_HOST' in os.environ):
        local_dev_config = optional('components/env/dev-local.py')

    include(
            # local settings (do not commit to version control)
            optional(os.path.join(os.getcwd(), 'local_settings.py')),

            'components/base.py',
            'components/logging.py',
            'components/celery.py',
            'components/rest_framework.py',

            # Override settings for testing:
            # optional('components/testing.py'),

            # Missing file:
            # optional('components/missing_file.py'),

            # Assigned if EP/SECURE_IMPORTER are run on the host machine
            local_dev_config,

            # hostname-based override, in settings/env/ directory
            optional('components/env/%s.py' % socket.gethostname().split('.', 1)[0]),

            scope=globals()
    )
