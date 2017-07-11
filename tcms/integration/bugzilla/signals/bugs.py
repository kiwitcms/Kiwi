# -*- coding: utf-8 -*-
import threading
import warnings

import xmlrpclib

from django.conf import settings


class BZ_Externer_Track_Thread(threading.Thread):
    def __init__(self, bug, is_add):
        self.bug = bug
        self.is_add = is_add
        threading.Thread.__init__(self)

    def run(self):
        if self.is_add:
            try:
                proxy = xmlrpclib.ServerProxy(settings.BUGZILLA3_RPC_SERVER)
                proxy.ExternalBugs.add_external_bug({
                    'Bugzilla_login': settings.BUGZILLA_USER,
                    'Bugzilla_password': settings.BUGZILLA_PASSWORD,
                    'bug_ids': [self.bug.bug_id, ],
                    'external_bugs': [
                        {'ext_bz_bug_id': str(self.bug.case.case_id),
                         'ext_type_description': 'TCMS Test Case'}, ]
                })
            except Exception as err:
                message = '%s: %s' % (err.__class__.__name__, err)
                warnings.warn(message)
        else:
            pass


# Bug add listen for bugzilla
def bug_added_bz_handler(sender, *args, **kwargs):
    bug = kwargs['instance']
    is_add = True
    if bug.case:
        # signal is raise by testcase
        BZ_Externer_Track_Thread(bug, is_add).start()
    else:
        # signal is raise by testcase
        return
