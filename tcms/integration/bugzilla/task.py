# -*- coding: utf-8 -*-
import warnings

import xmlrpclib

from celery import shared_task
from django.conf import settings


@shared_task
def bugzilla_external_track(bug):
    if bug.bug_system.pk == settings.DEFAULT_BUG_SYSTEM_ID:
        try:
            proxy = xmlrpclib.ServerProxy(settings.BUGZILLA3_RPC_SERVER)
            proxy.ExternalBugs.add_external_bug({
                'Bugzilla_login': settings.BUGZILLA_USER,
                'Bugzilla_password': settings.BUGZILLA_PASSWORD,
                'bug_ids': [int(bug.bug_id), ],
                'external_bugs': [{'ext_bz_bug_id': str(bug.case.case_id),
                                   'ext_type_description': 'TCMS Test Case'}, ]
            })
        except Exception as err:
            message = '%s: %s' % (err.__class__.__name__, str(err))
            warnings.warn(message)
