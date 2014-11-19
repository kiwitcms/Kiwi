# -*- coding: utf-8 -*-
from django.core.management import call_command
from django_nose.runner import NoseTestSuiteRunner


class NitrateTestSuiteRunner(NoseTestSuiteRunner):
    def setup_databases(self):
        # create test database and schemas
        original = super(NitrateTestSuiteRunner, self).setup_databases()

        # load initial fixtures
        call_command('loaddata', 'initial_data', verbosity=0,
                     skip_validation=True)

        # load unittest fixtures
        call_command('loaddata', 'unittest', verbosity=0,
                     skip_validation=True)

        # load custom fixtures

        return original