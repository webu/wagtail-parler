#!/usr/bin/env python
# Standard libs
import os
import sys

# Django imports
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ["DJANGO_SETTINGS_MODULE"] = "wagtail_parler_tests.settings"
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(failfast=True)
    failures = test_runner.run_tests(["wagtail_parler_tests"])
    sys.exit(bool(failures))
