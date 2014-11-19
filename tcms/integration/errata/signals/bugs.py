# -*- coding: utf-8 -*-
from datetime import datetime

from tcms.integration.messaging import MessagingProducer as p


# Bug add listen for qpid
def bug_added_handler(sender, *args, **kwargs):
    tcr_bug = kwargs['instance']
    if tcr_bug.case_run:
        # signal is raise by testcaserun
        tr = tcr_bug.case_run.run
    else:
        # signal is raise by testcase
        return
    if tr.errata_id:
        qpid_bug_add = {
            "run_id": tr.run_id,
            "errata_id": tr.errata_id,
            "bug_id": tcr_bug.bug_id,
            "when": datetime.now().strftime("%Y-%m-%d %X"),
        }
        # qpid message send
        try:
            p().send(qpid_bug_add, "bugs.added", False)
        except:
            pass
    else:
        # FIXME
        pass


# Bug remove listen for qpid
def bug_removed_handler(sender, *args, **kwargs):
    tcr_bug = kwargs['instance']
    if tcr_bug.case_run:
        # signal is raise by testcaserun
        tr = tcr_bug.case_run.run
    else:
        # signal is raise by testcase
        return
    if tr.errata_id:
        qpid_bug_remove = {
            "run_id": tr.run_id,
            "errata_id": tr.errata_id,
            "bug_id": tcr_bug.bug_id,
            "when": datetime.now().strftime("%Y-%m-%d %X"),
        }
        # qpid message send
        try:
            p().send(qpid_bug_remove, "bugs.dropped", False)
        except:
            pass
    else:
        # FIXME
        pass
