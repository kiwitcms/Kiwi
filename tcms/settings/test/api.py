from tcms.settings.test import *  # noqa: F403


INSTALLED_APPS += ('django_nose',)  # noqa: F405

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
