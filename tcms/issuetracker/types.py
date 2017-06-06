import os
import urllib
import bugzilla
import bugzilla_integration
from django.conf import settings
from django.core.urlresolvers import reverse


class IssueTrackerType(object):
    """
        Represents actions which can be performed with issue trackers.
        This is a common interfce for all issue trackers that KiwiTestPad
        supports!
    """

    def __init__(self, tracker):
        """
            @tracker - TestCaseBugSystem object
        """
        self.tracker = tracker

    @classmethod
    def from_name(cls, name):
        """
            Return the class which matches @name if it exists inside this
            module or raise an exception.
        """
        if name not in globals():
            raise NotImplementedError('IT of type %s is not supported' % name)
        return globals()[name]

    def report_issue_from_testcase(self, caserun):
        """
            When merking results inside a test case run there is a
            'Report' link. When clicked this method is called to automatically
            report new issue and provide all the details, like steps to reproduce,
            from the test case.

            @caserun - TestCaseRun object
        """
        raise NotImplementedError()

    def add_testcase_to_issue(self, testcases, issue):
        """
            When adding issues to test case run results there is a
            'Check to add test cases to Issue tracker' checkbox. If
            checked this method is called to link the bug report to the
            test case which was used to discover the bug.

            @testcases - list of TestCase objects
            @issue - TestCaseBug object
        """
        raise NotImplementedError()

    def all_issues_link(self, ids):
        """
            Used in testruns.views.get() aka run/report.html to produce
            a single URL which will open all reported issues into a single
            page in the Issue tracker. For example Bugzilla supports listing
            multiple bugs into a table. GitHub on the other hand doesn't
            support this functionality.

            @ids - list if issues reported against test case runs

            @return - None if not suported or string representing the URL
        """
        return None


class Bugzilla(IssueTrackerType):
    def __init__(self, tracker):
        super(Bugzilla, self).__init__(tracker)

        # directory for Bugzilla credentials
        bugzilla_cache_dir = '/tmp/.bugzilla/'
        if not os.path.exists(bugzilla_cache_dir):
            os.makedirs(bugzilla_cache_dir, 0o700)

        # passing user & password will attemt to authenticate
        # when the __init__ method runs. Do it here so that we don't
        # have to do it everywhere else where it might be needed.
        self.rpc = bugzilla.Bugzilla(
            tracker.api_url,
            user=self.tracker.api_username,
            password=self.tracker.api_password,
            cookiefile=bugzilla_cache_dir + 'cookie',
            tokenfile=bugzilla_cache_dir + 'token',
        )

    def add_testcase_to_issue(self, testcases, issue):
        for case in testcases:
            bugzilla_integration.BugzillaThread(self.rpc, case, issue).start()

    def all_issues_link(self, ids):
        if not self.tracker.report_url:
            return None

        if not self.tracker.report_url.endswith('/'):
            self.tracker.report_url += '/'

        return self.tracker.report_url + 'buglist.cgi?bugidtype=include&bug_id=%s' % ','.join(ids)

    def report_issue_from_test_case(self, caserun):
        # because of circular dependencies
        from tcms.testcases.models import TestCaseText

        args = {}
        args['cf_build_id'] = caserun.run.build.name

        txt = caserun.get_text_with_version(case_text_version=caserun.case_text_version)

        if txt and isinstance(txt, TestCaseText):
            plain_txt = txt.get_plain_text()

            setup = plain_txt.setup
            action = plain_txt.action
            effect = plain_txt.effect
        else:
            setup = 'None'
            action = 'None'
            effect = 'None'

        caserun_url = settings.KIWI_BASE_URL + \
            reverse('testruns-get', args=[caserun.run.pk])

        comment = "Filed from caserun %s\n\n" % caserun_url
        comment += "Version-Release number of selected " \
                   "component (if applicable):\n"
        comment += '%s\n\n' % caserun.build.name
        comment += "Steps to Reproduce: \n%s\n%s\n\n" % (setup, action)
        comment += "Actual results: \n<describe what happened>\n\n"
        comment += "Expected results:\n%s\n\n" % effect

        args['comment'] = comment
        args['component'] = caserun.case.component.values_list('name',
                                                               flat=True)
        args['product'] = caserun.run.plan.product.name
        args['short_desc'] = 'Test case failure: %s' % caserun.case.summary
        args['version'] = caserun.run.product_version

        url = self.tracker.report_url
        if not url.endswith('/'):
            url += '/'

        return url + 'enter_bug.cgi?' + urllib.urlencode(args, True)


class JIRA(IssueTrackerType):
    def all_issues_link(self, ids):
        if not self.tracker.report_url:
            return None

        if not self.tracker.report_url.endswith('/'):
            self.tracker.report_url += '/'

        return self.tracker.report_url + 'issues/?jql=issueKey%%20in%%20(%s)' % '%2C%20'.join(ids)
