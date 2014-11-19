# -*- coding: utf-8 -*-
from datetime import datetime

from tcms.integration.messaging import MessagingProducer as p


# new testrun created info for qpid
def testrun_created_handler(sender, *args, **kwargs):
    ''' Sending current TestRun newly created '''

    tr = kwargs['instance']
    if kwargs.get('created'):
        run_create_info = {
            "plan_id": tr.plan_id,
            "run_id": tr.run_id,
            "errata_id": tr.errata_id,
            "when": datetime.now().strftime("%Y-%m-%d %X")
        }
        try:
            p().send(run_create_info, "testrun.created", False)
        except:
            pass

    else:
        # FIXME: Log, Plugin and other editing functions
        pass


# testrun progress/finish info for qpid
def testrun_progress_handler(sender, *args, **kwargs):
    ''' Sending the progress of current TestRun '''

    tcr = kwargs['instance']
    tr = tcr.run
    if not kwargs.get('created'):
        # testrun is progress
        run_info = {
            "plan_id": tr.plan_id,
            "run_id": tr.run_id,
            "errata_id": tr.errata_id,
            "when": datetime.now().strftime("%Y-%m-%d %X"),
        }

        if not tr.check_all_case_runs():
            # testrun is progress
            completed_percent = str(tr.completed_case_run_percent) + "%"
            run_info["completed_percent"] = completed_percent
            try:
                p().send(run_info, "testrun.progress", False)
            except:
                pass

        else:
            # testrun is finished
            try:
                p().send(run_info, "testrun.finished", False)
            except:
                pass
    else:
        # FIXME: log, plugin and other editing functions
        pass
