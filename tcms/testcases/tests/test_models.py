# -*- coding: utf-8 -*-

from __future__ import absolute_import

from mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.db.models.signals import post_save, post_delete, pre_save

from ..models import TestCaseBugSystem
from ..models import TestCaseText
from tcms.core.utils.checksum import checksum
from tcms.testcases import signals as case_watchers
from tcms.testcases.models import TestCase
from tcms.testcases.models import _listen
from tcms.tests import BasePlanCase
from tcms.tests.factories import ComponentFactory
from tcms.tests.factories import TestBuildFactory
from tcms.tests.factories import TestCaseComponentFactory
from tcms.tests.factories import TestCaseEmailSettingsFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestCaseRunFactory
from tcms.tests.factories import TestCaseTagFactory
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import TestTagFactory


class TestCaseRemoveBug(BasePlanCase):
    """Test TestCase.remove_bug"""

    @classmethod
    def setUpTestData(cls):
        super(TestCaseRemoveBug, cls).setUpTestData()
        cls.build = TestBuildFactory(product=cls.product)
        cls.test_run = TestRunFactory(product_version=cls.version, plan=cls.plan,
                                      manager=cls.tester, default_tester=cls.tester)
        cls.case_run = TestCaseRunFactory(assignee=cls.tester, tested_by=cls.tester,
                                          case=cls.case, run=cls.test_run, build=cls.build)
        cls.bug_system = TestCaseBugSystem.objects.get(name='Bugzilla')

    def setUp(self):
        self.bug_id_1 = '12345678'
        self.case.add_bug(self.bug_id_1, self.bug_system.pk,
                          summary='error when add a bug to a case')
        self.bug_id_2 = '10000'
        self.case.add_bug(self.bug_id_2, self.bug_system.pk, case_run=self.case_run)

    def tearDown(self):
        self.case.case_bug.all().delete()

    def test_remove_case_bug(self):
        self.case.remove_bug(self.bug_id_1)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_1).exists()
        self.assertFalse(bug_found)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_2).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_2))

    def test_case_bug_not_removed_by_passing_case_run(self):
        self.case.remove_bug(self.bug_id_1, run_id=self.case_run.pk)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_1).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_1))

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_2).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_2))

    def test_remove_case_run_bug(self):
        self.case.remove_bug(self.bug_id_2, run_id=self.case_run.pk)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_2).exists()
        self.assertFalse(bug_found)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_1).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_1))

    def test_case_run_bug_not_removed_by_missing_case_run(self):
        self.case.remove_bug(self.bug_id_2)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_1).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_1))

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_2).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_2))


class TestCaseRemoveComponent(BasePlanCase):
    """Test TestCase.remove_component"""

    @classmethod
    def setUpTestData(cls):
        super(TestCaseRemoveComponent, cls).setUpTestData()

        cls.component_1 = ComponentFactory(name='Application',
                                           product=cls.product,
                                           initial_owner=cls.tester,
                                           initial_qa_contact=cls.tester)
        cls.component_2 = ComponentFactory(name='Database',
                                           product=cls.product,
                                           initial_owner=cls.tester,
                                           initial_qa_contact=cls.tester)

        cls.cc_rel_1 = TestCaseComponentFactory(case=cls.case,
                                                component=cls.component_1)
        cls.cc_rel_2 = TestCaseComponentFactory(case=cls.case,
                                                component=cls.component_2)

    def test_remove_a_component(self):
        self.case.remove_component(self.component_1)

        found = self.case.component.filter(pk=self.component_1.pk).exists()
        self.assertFalse(
            found,
            'Component {0} exists. But, it should be removed.'.format(
                self.component_1.pk))
        found = self.case.component.filter(pk=self.component_2.pk).exists()
        self.assertTrue(
            found,
            'Component {0} does not exist. It should not be removed.'.format(
                self.component_2.pk))


class TestCaseRemovePlan(BasePlanCase):
    """Test TestCase.remove_plan"""

    @classmethod
    def setUpTestData(cls):
        super(TestCaseRemovePlan, cls).setUpTestData()

        cls.new_case = TestCaseFactory(author=cls.tester, default_tester=None, reviewer=cls.tester,
                                       plan=[cls.plan])

    def test_remove_plan(self):
        self.new_case.remove_plan(self.plan)

        found = self.plan.case.filter(pk=self.new_case.pk).exists()
        self.assertFalse(
            found, 'Case {0} should has no relationship to plan {0} now.'.format(self.new_case.pk,
                                                                                 self.plan.pk))


class TestCaseRemoveTag(BasePlanCase):
    """Test TestCase.remove_tag"""

    @classmethod
    def setUpTestData(cls):
        super(TestCaseRemoveTag, cls).setUpTestData()

        cls.tag_rhel = TestTagFactory(name='rhel')
        cls.tag_fedora = TestTagFactory(name='fedora')
        TestCaseTagFactory(case=cls.case, tag=cls.tag_rhel, user=cls.tester.pk)
        TestCaseTagFactory(case=cls.case, tag=cls.tag_fedora, user=cls.tester.pk)

    def test_remove_tag(self):
        self.case.remove_tag(self.tag_rhel)

        tag_pks = list(self.case.tag.all().values_list('pk', flat=True))
        self.assertEqual([self.tag_fedora.pk], tag_pks)


class TestGetPlainText(BasePlanCase):
    """Test TestCaseText.get_plain_text"""

    @classmethod
    def setUpTestData(cls):
        super(TestGetPlainText, cls).setUpTestData()

        cls.action = '<p>First step:</p>'
        cls.effect = '''<ul>
    <li>effect 1</li>
    <li>effect 2</li>
</ul>'''
        cls.setup = '<p><a href="/setup_guide">setup</a></p>'
        cls.breakdown = '<span>breakdown</span>'

        cls.text_author = User.objects.create_user(username='author',
                                                   email='my@example.com')
        TestCaseText.objects.create(
            case=cls.case,
            case_text_version=1,
            author=cls.text_author,
            action=cls.action,
            effect=cls.effect,
            setup=cls.setup,
            breakdown=cls.breakdown,
            action_checksum=checksum(cls.action),
            effect_checksum=checksum(cls.effect),
            setup_checksum=checksum(cls.setup),
            breakdown_checksum=checksum(cls.breakdown))

    def test_get_plain_text(self):
        case_text = TestCaseText.objects.all()[0]
        plain_text = case_text.get_plain_text()

        # These expected values were converted from html2text.
        self.assertEqual('First step:', plain_text.action)
        self.assertEqual('  * effect 1\n  * effect 2', plain_text.effect)
        self.assertEqual('[setup](/setup_guide)', plain_text.setup)
        self.assertEqual('breakdown', plain_text.breakdown)


class FakeThread(object):
    """Fake Thread to mock threading.Thread"""

    def __init__(self, target=None, args=(), kwargs={}):
        self.target = target
        self.args = args
        self.kwargs = kwargs

    def setDaemon(self, value):
        """Do nothing"""

    def start(self):
        self.target(*self.args, **self.kwargs)


class TestSendMailOnCaseIsUpdated(BasePlanCase):
    """Test send mail on case post_save signal is triggered"""

    def setUp(self):
        super(TestSendMailOnCaseIsUpdated, self).setUp()
        _listen()

    def tearDown(self):
        post_save.disconnect(case_watchers.on_case_save, TestCase)
        post_delete.disconnect(case_watchers.on_case_delete, TestCase)
        pre_save.disconnect(case_watchers.pre_save_clean, TestCase)
        super(TestSendMailOnCaseIsUpdated, self).tearDown()

    @classmethod
    def setUpTestData(cls):
        super(TestSendMailOnCaseIsUpdated, cls).setUpTestData()

        cls.case.add_text('action', 'effect', 'setup', 'breakdown')

        cls.email_setting = TestCaseEmailSettingsFactory(
            case=cls.case,
            notify_on_case_update=True,
            auto_to_case_author=True)

        cls.case_editor = User.objects.create_user(username='editor')
        # This is actually done when update a case. Setting current_user
        # explicitly here aims to mock that behavior.
        cls.case.current_user = cls.case_editor

    @patch('tcms.core.utils.mailto.threading.Thread', new=FakeThread)
    def test_send_mail_to_case_author(self):
        self.case.summary = 'New summary for running test'
        self.case.save()

        expected_mail_body = '''TestCase [{0}] has been updated by {1}

Case -
{2}?#log

--
Configure mail: {2}/edit/
------- You are receiving this mail because: -------
You have subscribed to the changes of this TestCase
You are related to this TestCase'''.format(self.case.summary,
                                           'editor',
                                           self.case.get_url())

        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(expected_mail_body, mail.outbox[0].body)
        self.assertEqual([self.case.author.email], mail.outbox[0].to)
