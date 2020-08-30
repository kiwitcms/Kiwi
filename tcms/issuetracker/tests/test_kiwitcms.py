# pylint: disable=attribute-defined-outside-init, wrong-import-position

import os
import unittest

from django.conf import settings

if 'tcms.bugs.apps.AppConfig' not in settings.INSTALLED_APPS:
    raise unittest.SkipTest('tcms.bugs is disabled')

from django.contrib.sites.models import Site
from django.template.loader import render_to_string

from tcms.bugs.models import Bug
from tcms.core.contrib.linkreference.models import LinkReference
from tcms.core.helpers.comments import get_comments
from tcms.issuetracker.types import KiwiTCMS
from tcms.rpc.tests.utils import APITestCase
from tcms.testcases.models import BugSystem

from tcms.bugs.tests.factory import BugFactory
from tcms.tests.factories import ComponentFactory
from tcms.tests.factories import TestExecutionFactory


@unittest.skipUnless(os.getenv('TEST_BUGTRACKER_INTEGRATION'),
                     'Bug tracker integration testing not enabled')
class TestKiwiTCMSIntegration(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.existing_bug = BugFactory()

        self.execution_1 = TestExecutionFactory()
        self.execution_1.case.text = "Given-When-Then"
        self.execution_1.case.save()  # will generate history object

        self.component = ComponentFactory(name='KiwiTCMS integration',
                                          product=self.execution_1.run.plan.product)
        self.execution_1.case.add_component(self.component)

        self.base_url = "https://%s" % Site.objects.get(id=settings.SITE_ID).domain
        # note: ^^^ this is https just because .get_full_url() default to that !
        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name='KiwiTCMS internal bug tracker',
            tracker_type='tcms.issuetracker.types.KiwiTCMS',
            base_url=self.base_url
        )
        self.integration = KiwiTCMS(bug_system, None)

    def test_bug_id_from_url(self):
        result = self.integration.bug_id_from_url(self.existing_bug.get_full_url())
        self.assertEqual(self.existing_bug.pk, result)

    def test_details_for_url(self):
        result = self.integration.details(self.existing_bug.get_full_url())

        self.assertEqual(self.existing_bug.summary, result['title'])

        expected_description = render_to_string(
            'include/bug_details.html',
            {'object': self.existing_bug})
        self.assertEqual(expected_description, result['description'])

    def test_auto_update_bugtracker(self):
        # make sure bug is not associated with execution
        self.assertFalse(
            self.existing_bug.executions.filter(pk=self.execution_1.pk).exists())

        # simulate user adding a new bug URL to a TE and clicking
        # 'Automatically update bug tracker'
        result = self.rpc_client.TestExecution.add_link({
            'execution_id': self.execution_1.pk,
            'is_defect': True,
            'url': self.existing_bug.get_full_url(),
        }, True)

        # making sure RPC above returned the same URL
        self.assertEqual(self.existing_bug.get_full_url(), result['url'])

        # bug is now associated with execution
        self.assertTrue(
            self.existing_bug.executions.filter(pk=self.execution_1.pk).exists())

    def test_report_issue_from_test_execution_1click_works(self):
        # simulate user clicking the 'Report bug' button in TE widget, TR page
        result = self.rpc_client.Bug.report(self.execution_1.pk, self.integration.bug_system.pk)
        self.assertEqual(result['rc'], 0)
        self.assertIn(self.integration.bug_system.base_url, result['response'])
        self.assertIn('/bugs/', result['response'])

        new_bug_id = self.integration.bug_id_from_url(result['response'])
        bug = Bug.objects.get(pk=new_bug_id)

        self.assertEqual("Failed test: %s" % self.execution_1.case.summary, bug.summary)
        first_comment = get_comments(bug).first()
        for expected_string in [
                "Filed from execution %s" % self.execution_1.get_full_url(),
                self.execution_1.run.plan.product.name,
                self.component.name,
                "Steps to reproduce",
                self.execution_1.case.text]:
            self.assertIn(expected_string, first_comment.comment)

        # verify that LR has been added to TE
        self.assertTrue(LinkReference.objects.filter(
            execution=self.execution_1,
            url=result['response'],
            is_defect=True,
        ).exists())

    def test_empty_details_when_bug_dont_exist(self):
        non_existing_bug_id = -1
        self.assertFalse(Bug.objects.filter(pk=non_existing_bug_id).exists())

        result = self.integration.details("{}/{}".format(self.base_url, non_existing_bug_id))
        self.assertEqual(result, {})
