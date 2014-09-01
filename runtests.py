#!/usr/bin/env python
import os
import sys

import django
from django.conf import settings


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
               'ENGINE': 'django.db.backends.sqlite3',
            }
        },
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.admin',
            'census',
        )
    )

# Compatibility with Django 1.7's stricter initialization
if hasattr(django, 'setup'):
    django.setup()

def runtests(args=None):
    try:
        from django.test.simple import DjangoTestSuiteRunner
    except ImportError:
        from django.test import DjangoTestSuiteRunner
    test_runner = DjangoTestSuiteRunner(verbosity=1)
    failures = test_runner.run_tests(['census', ])
    sys.exit(failures)


if __name__ == '__main__':
    runtests(sys.argv)