# -*- coding: utf-8 -*-

from six.moves import urllib
# The following was obtained by clicking on "Remember values as
# bookmarkable template" in Bugzilla:
from tcms.testcases.models import TestCaseText


class BugTracker(object):
    """
    Abstract base class representing an external bug tracking system
    """

    def make_url(self, caserun):
        raise NotImplementedError


class Bugzilla(BugTracker):
    def __init__(self, base_url):
        self.base_url = base_url

    def make_url(self, run, caserun, case_text_version):
        args = {}
        args['cf_build_id'] = run.build.name

        txt = caserun.get_text_with_version(
            case_text_version=case_text_version)

        if txt and isinstance(txt, TestCaseText):
            plain_txt = txt.get_plain_text()

            setup = plain_txt.setup
            action = plain_txt.action
            effect = plain_txt.effect
        else:
            setup = 'None'
            action = 'None'
            effect = 'None'

        comment = "Filed from caserun (INSERT URL HERE)\n\n"
        comment += "Version-Release number of selected " \
                   "component (if applicable):\n"
        comment += '%s\n\n' % caserun.build.name
        comment += "Steps to Reproduce: \n%s\n%s\n\n" % (setup, action)
        # FIXME+ caseinfo['actual_results'] + "\n\n"
        comment += "Actual results: \n#FIXME\n\n"
        comment += "Expected results:\n%s\n\n" % effect
        args['comment'] = comment
        args['component'] = caserun.case.component.values_list('name',
                                                               flat=True)
        args['op_sys'] = 'Linux'
        args['product'] = run.plan.product.name
        args['short_desc'] = 'Test case failure: %s' % caserun.case.summary
        args['version'] = run.product_version
        # this should set the "only visible to Red Hat Quality Assurance (
        # internal)" flag, but don't go filing this example bug.
        args['bit-11'] = '1'

        return self.base_url + 'enter_bug.cgi?' + urllib.parse.urlencode(args, True)


cr = {
    'case_id': 42,
    'build_name': 'THIS IS THE BUILD ID',
    'actions': 'Phase 1: Collect Underpants\nPhase 2: ?\nPhase 3: Profit!\n',
    'expected_results': 'Profit!',
    'actual_results': 'Kenny died',
    'component': 'evolution',
    'product': 'Red Hat Enterprise Linux 5',
    'summary': 'This is a test case summary',
    'version': '5.4',
}
