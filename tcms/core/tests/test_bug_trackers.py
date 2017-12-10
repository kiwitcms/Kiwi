# -*- coding: utf-8 -*-

from six.moves.urllib_parse import urlparse
from six.moves.urllib_parse import parse_qs

from tcms.core.utils.bugtrackers import Bugzilla
from tcms.tests import BaseCaseRun


class TestBugzillaMakeURL(BaseCaseRun):
    """Test Bugzilla.make_url"""

    @classmethod
    def setUpTestData(cls):
        super(TestBugzillaMakeURL, cls).setUpTestData()

        cls.case_1.add_text('action', 'effect', 'setup', 'breakdown')

    def test_use_correct_bz_base_url(self):
        bz = Bugzilla('http://localhost/bugzilla')
        url = bz.make_url(self.test_run, self.case_run_1, 1)

        url_parts = urlparse(url)
        self.assertEqual('http', url_parts.scheme)
        self.assertEqual('localhost', url_parts.netloc)
        self.assertTrue(url_parts.path.startswith('/bugzilla'))

    def test_comment_with_plain_text(self):
        bz = Bugzilla('http://localhost/bugzilla')
        url = bz.make_url(self.test_run, self.case_run_1, 1)

        url_parts = urlparse(url)

        expected_comment = '''Filed from caserun (INSERT URL HERE)

Version-Release number of selected component (if applicable):
{build_name}

Steps to Reproduce:
{setup}
{action}

Actual results:
#FIXME

Expected results:
{effect}

'''.format(build_name=self.case_run_1.build.name,
           setup='setup', action='action', effect='effect')
        self.assertEqual(expected_comment,
                         parse_qs(url_parts.query)['comment'][0])

    def test_short_desc(self):
        bz = Bugzilla('http://localhost/bugzilla')
        url = bz.make_url(self.test_run, self.case_run_1, 1)

        url_parts = urlparse(url)
        self.assertEqual(
            'Test case failure: {}'.format(self.case_run_1.case.summary),
            parse_qs(url_parts.query)['short_desc'][0])
