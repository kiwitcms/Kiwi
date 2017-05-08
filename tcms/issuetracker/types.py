import bugzilla_integration


class IssueTrackerType(object):
    """
        Represents actions which can be performed with issue trackers.
        This is a common interfce for all issue trackers that Nitrate
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

    def report_issue_from_testcase(self, testcase):
        """
            When merking results inside a test case run there is a
            'Report' link. When clicked this method is called to automatically
            report new issue and provide all the details, like steps to reproduce,
            from the test case.

            @testcase - TestCase object
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
    def add_testcase_to_issue(self, testcases, issue):
        for case in testcases:
            bugzilla_integration.add_bug_to_bugzilla(self.tracker, case, issue)

    def all_issues_link(self, ids):
        if not self.tracker.report_url:
            return None

        if not self.tracker.report_url.endswith('/'):
            self.tracker.report_url += '/'

        return self.tracker.report_url + 'buglist.cgi?bugidtype=include&bug_id=%s' % ','.join(ids)


class JIRA(IssueTrackerType):
    def all_issues_link(self, ids):
        if not self.tracker.report_url:
            return None

        if not self.tracker.report_url.endswith('/'):
            self.tracker.report_url += '/'

        return self.tracker.report_url + 'issues/?jql=issueKey%%20in%%20(%s)' % '%2C%20'.join(ids)
