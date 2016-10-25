INSTALLED_APPS += ('django_jenkins',)

PROJECT_APPS = ('ep',)

JENKINS_TASKS = (
    # 'django_jenkins.tasks.with_coverage',
    # 'django_jenkins.tasks.run_pep8',
    # 'django_jenkins.tasks.run_pyflakes',
)

ALLOWED_HOSTS = ['dev.iodicus.net', 'localhost', ]

import sys

# - See more at: http://www.celerity.com/blog/2013/04/29/how-write-speedy-unit-tests-django-part-1-basics/#sthash.9vDnOgRl.dpuf
if 'test' in sys.argv: DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
