# pylint: disable=attribute-defined-outside-init

import os
import unittest
from urllib.parse import urlencode

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.issuetracker.types import Bugzilla
from tcms.management.models import Version
from tcms.rpc.tests.utils import APITestCase
from tcms.testcases.models import BugSystem

from tcms.tests.factories import ComponentFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestExecutionFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestRunFactory


@unittest.skipUnless(os.getenv('TEST_BUGTRACKER_INTEGRATION'),
                     'Bug tracker integration testing not enabled')
class TestBugzillaIntegration(APITestCase):
    existing_bug_id = 1
    existing_bug_url = 'http://bugtracker.kiwitcms.org/bugzilla/show_bug.cgi?id=1'

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution_1 = TestExecutionFactory()

        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name='Dockerized Bugzilla',
            tracker_type='tcms.issuetracker.types.Bugzilla',
            base_url='http://bugtracker.kiwitcms.org/bugzilla/',
            api_url='http://bugtracker.kiwitcms.org/bugzilla/xmlrpc.cgi',
            api_username='admin@bugzilla.bugs',
            api_password='password',
        )
        self.integration = Bugzilla(bug_system, None)

    def test_bug_id_from_url(self):
        result = self.integration.bug_id_from_url(self.existing_bug_url)
        self.assertEqual(self.existing_bug_id, result)

    def test_details(self):
        result = self.integration.details(self.existing_bug_url)

        # Bugzilla doesn't support OpenGraph and ATM we don't provide
        # additional integration here
        # warning:    this vvv is not the regular - (dash) character
        self.assertEqual('1 – Hello World', result['title'])
        self.assertEqual('', result['description'])
        self.assertEqual('', result['image'])

    def test_auto_update_bugtracker(self):
        bug = self.integration.rpc.getbug(self.existing_bug_id)

        # make sure there are no comments to confuse the test
        for comment in bug.getcomments():
            self.assertNotIn('Confirmed via test execution', comment['text'])

        # simulate user adding a new bug URL to a TE and clicking
        # 'Automatically update bug tracker'
        result = self.rpc_client.TestExecution.add_link({
            'execution_id': self.execution_1.pk,
            'is_defect': True,
            'url': self.existing_bug_url,
        }, True)

        # making sure RPC above returned the same URL
        self.assertEqual(self.existing_bug_url, result['url'])

        # assert that a comment has been added as the last one
        # and also verify its text
        bug.refresh()
        last_comment = bug.getcomments()[-1]
        for expected_string in [
                'Confirmed via test execution',
                "TR-%d: %s" % (self.execution_1.run_id, self.execution_1.run.summary),
                self.execution_1.run.get_full_url(),
                "TE-%d: %s" % (self.execution_1.pk, self.execution_1.case.summary)]:
            self.assertIn(expected_string, last_comment['text'])

    def test_report_issue_from_test_execution_falls_back_to_query_params(self):
        """
            In case 1-click bug-report fails Bugzilla integration will open
            a URL with some of the fields pre-defined so the tester will have
            an easier time filling in the rest.
        """
        # note: automatically creates a version called 'unspecified'
        product = ProductFactory(name='Kiwi TCMS')
        version, _ = Version.objects.get_or_create(product=product, value='unspecified')
        component = ComponentFactory(name='Bugzilla integration', product=product)

        test_plan = TestPlanFactory(product=product, product_version=version)
        test_case = TestCaseFactory(component=[component], plan=[test_plan])
        test_case.save()  # will generate history object

        test_run = TestRunFactory(plan=test_plan, product_version=version)
        execution2 = TestExecutionFactory(run=test_run, case=test_case, build=test_run.build)

        # simulate user clicking the 'Report bug' button in TE widget, TR page
        result = self.rpc_client.Bug.report(execution2.pk, self.integration.bug_system.pk)
        self.assertEqual(result['rc'], 0)
        self.assertIn('http://bugtracker.kiwitcms.org/bugzilla/enter_bug.cgi', result['response'])

        # assert that the result looks like valid URL parameters
        self.assertIn('product=Kiwi+TCMS', result['response'])
        self.assertIn('component=Bugzilla+integration', result['response'])
        self.assertIn('version=unspecified', result['response'])
        expected_description = urlencode({
            'short_desc': "Test case failure: %s" % execution2.case.summary,
        })
        self.assertIn(expected_description, result['response'])

    def test_report_issue_from_test_execution_1click_works(self):
        """
            Automatic 1-click bug report to Bugzilla usually works
            when Product, Version and Component exist in Bugzilla!
        """
        # note: automatically creates a version called 'unspecified'
        product = ProductFactory(name='TestProduct')
        version, _ = Version.objects.get_or_create(product=product, value='unspecified')
        component = ComponentFactory(name='TestComponent', product=product)

        test_plan = TestPlanFactory(product=product, product_version=version)
        test_case = TestCaseFactory(component=[component], plan=[test_plan])
        test_case.save()  # will generate history object

        test_run = TestRunFactory(plan=test_plan, product_version=version)
        execution2 = TestExecutionFactory(run=test_run, case=test_case, build=test_run.build)

        # simulate user clicking the 'Report bug' button in TE widget, TR page
        result = self.rpc_client.Bug.report(execution2.pk, self.integration.bug_system.pk)
        self.assertEqual(result['rc'], 0)
        self.assertIn(
            'http://bugtracker.kiwitcms.org/bugzilla/show_bug.cgi?id=', result['response'])

        new_bug_id = self.integration.bug_id_from_url(result['response'])
        bug = self.integration.rpc.getbug(new_bug_id)

        self.assertEqual('TestProduct', bug.product)
        self.assertEqual('TestComponent', bug.component)
        self.assertEqual('unspecified', bug.version)
        self.assertEqual('All', bug.op_sys)
        self.assertEqual('All', bug.rep_platform)

        last_comment = bug.getcomments()[-1]
        for expected_string in [
                "Filed from execution %s" % execution2.get_full_url(),
                product.name,
                component.name,
                test_case.text]:
            self.assertIn(expected_string, last_comment['text'])

        # verify that LR has been added to TE
        self.assertTrue(LinkReference.objects.filter(
            execution=execution2,
            url=result['response'],
            is_defect=True,
        ).exists())
