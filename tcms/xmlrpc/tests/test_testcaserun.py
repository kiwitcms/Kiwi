# -*- coding: utf-8 -*-

import unittest

from datetime import datetime
from xmlrpclib import Fault

from django.test import TestCase
from django import test

from tcms.xmlrpc.api import testcaserun
from tcms.xmlrpc.tests.utils import make_http_request
from tcms.testruns.models import TestCaseRun
from tcms.testruns.models import TestCaseRunStatus
from tcms.testcases.models import TestCaseBugSystem

from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestCaseRunFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory
from tcms.tests.factories import TestBuildFactory
from tcms.xmlrpc.tests.utils import AssertMessage


class TestCaseRunCreate(test.TestCase):
    """Test testcaserun.create"""

    @classmethod
    def setUpClass(cls):
        super(TestCaseRunCreate, cls).setUpClass()
        cls.admin = UserFactory(username='tcr_admin', email='tcr_admin@example.com')
        cls.staff = UserFactory(username='tcr_staff', email='tcr_staff@example.com')
        cls.admin_request = make_http_request(user=cls.admin, user_perm='testruns.add_testcaserun')
        cls.staff_request = make_http_request(user=cls.staff)
        cls.product = ProductFactory(name='Nitrate')
        cls.version = VersionFactory(value='0.1', product=cls.product)
        cls.build = cls.product.build.all()[0]
        cls.plan = TestPlanFactory(author=cls.admin, owner=cls.admin, product=cls.product)
        cls.test_run = TestRunFactory(product_version=cls.version, build=cls.build,
                                      default_tester=None, plan=cls.plan)
        cls.case_run_status = TestCaseRunStatus.objects.get(name='IDLE')
        cls.case = TestCaseFactory(author=cls.admin, default_tester=None, plan=[cls.plan])

        cls.case_run_pks = []

    @classmethod
    def tearDownClass(cls):
        super(TestCaseRunCreate, cls).tearDownClass()
        TestCaseRun.objects.filter(pk__in=cls.case_run_pks).delete()
        cls.test_run.delete()
        cls.case.plan.clear()
        cls.case.delete()
        cls.plan.delete()
        cls.plan.type.delete()
        cls.version.delete()
        cls.product.build.all().delete()
        cls.product.delete()
        cls.product.classification.delete()
        cls.admin.delete()
        cls.staff.delete()

    def test_create_with_no_args(self):
        bad_args = (None, [], {}, (), 1, 0, -1, True, False, '', 'aaaa', object)
        for arg in bad_args:
            try:
                testcaserun.create(self.admin_request, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_create_with_no_required_fields(self):
        try:
            testcaserun.create(self.admin_request, {
                "assignee": self.staff.pk,
                "case_run_status": self.case_run_status.pk,
                "notes": "unit test 2"
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

        try:
            testcaserun.create(self.admin_request, {
                "build": self.build.pk,
                "assignee": self.staff.pk,
                "case_run_status": 1,
                "notes": "unit test 2"
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

        try:
            testcaserun.create(self.admin_request, {
                "run": self.test_run.pk,
                "build": self.build.pk,
                "assignee": self.staff.pk,
                "case_run_status": self.case_run_status.pk,
                "notes": "unit test 2"
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

    def test_create_with_required_fields(self):
        tcr = testcaserun.create(self.admin_request, {
            "run": self.test_run.pk,
            "build": self.build.pk,
            "case": self.case.pk,
            "case_text_version": 15,
        })
        self.assertIsNotNone(tcr)
        self.case_run_pks.append(tcr['case_run_id'])
        self.assertEqual(tcr['build_id'], self.build.pk)
        self.assertEqual(tcr['case_id'], self.case.pk)
        self.assertEqual(tcr['run_id'], self.test_run.pk)

    def test_create_with_all_fields(self):
        tcr = testcaserun.create(self.admin_request, {
            "run": self.test_run.pk,
            "build": self.build.pk,
            "case": self.case.pk,
            "assignee": self.admin.pk,
            "notes": "test_create_with_all_fields",
            "sortkey": 90,
            "case_run_status": self.case_run_status.pk,
            "case_text_version": 3,
        })
        self.assertIsNotNone(tcr)
        self.case_run_pks.append(tcr['case_run_id'])
        self.assertEquals(tcr['build_id'], self.build.pk)
        self.assertEquals(tcr['case_id'], self.case.pk)
        self.assertEquals(tcr['assignee_id'], self.admin.pk)
        self.assertEquals(tcr['notes'], "test_create_with_all_fields")
        self.assertEquals(tcr['sortkey'], 90)
        self.assertEquals(tcr['case_run_status'], 'IDLE')
        self.assertEquals(tcr['case_text_version'], 3)

    def test_create_with_non_exist_fields(self):
        try:
            testcaserun.create(self.admin_request, {
                "run": self.test_run.pk,
                "build": self.build.pk,
                "case": 111111,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_FOREIGN_KEY)

        try:
            testcaserun.create(self.admin_request, {
                "run": 11111,
                "build": self.build.pk,
                "case": self.case.pk,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_FOREIGN_KEY)

        try:
            testcaserun.create(self.admin_request, {
                "run": self.test_run.pk,
                "build": 11222222,
                "case": self.case.pk,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_FOREIGN_KEY)

    def test_create_with_chinese(self):
        tcr = testcaserun.create(self.admin_request, {
            "run": self.test_run.pk,
            "build": self.build.pk,
            "case": self.case.pk,
            "notes": "开源中国",
            "case_text_version": 2,
        })
        self.assertIsNotNone(tcr)
        self.case_run_pks.append(tcr['case_run_id'])
        self.assertEquals(tcr['build_id'], self.build.pk)
        self.assertEquals(tcr['case_id'], self.case.pk)
        self.assertEquals(tcr['assignee_id'], None)
        self.assertEquals(tcr['case_text_version'], 2)
        self.assertEquals(tcr['notes'], u"\u5f00\u6e90\u4e2d\u56fd")

    def test_create_with_long_field(self):
        large_str = """aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        """
        tcr = testcaserun.create(self.admin_request, {
            "run": self.test_run.pk,
            "build": self.build.pk,
            "case": self.case.pk,
            "notes": large_str,
            "case_text_version": 2,
        })
        self.assertIsNotNone(tcr)
        self.case_run_pks.append(tcr['case_run_id'])
        self.assertEquals(tcr['build_id'], self.build.pk)
        self.assertEquals(tcr['case_id'], self.case.pk)
        self.assertEquals(tcr['assignee_id'], None)
        self.assertEquals(tcr['case_text_version'], 2)
        self.assertEquals(tcr['notes'], large_str)

    def test_create_with_no_perm(self):
        try:
            testcaserun.create(self.staff_request, {
                "run": self.test_run.pk,
                "build": self.build.pk,
                "case": self.case.pk,
                "assignee": self.admin.pk,
                "notes": "test_create_with_all_fields",
                "sortkey": 2,
                "case_run_status": self.case_run_status.pk,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_PERMS)


class TestCaseRunAddComment(test.TestCase):
    """Test testcaserun.add_comment"""

    @classmethod
    def setUpClass(cls):
        super(TestCaseRunAddComment, cls).setUpClass()
        cls.admin = UserFactory(username='update_admin', email='update_admin@example.com')
        cls.admin_request = make_http_request(user=cls.admin,
                                              user_perm='testruns.change_testcaserun')

        cls.case_run_1 = TestCaseRunFactory()
        cls.case_run_2 = TestCaseRunFactory()

    @unittest.skip('TODO: not implemented yet.')
    def test_add_comment_with_no_args(self):
        pass

    @unittest.skip('TODO: not implemented yet.')
    def test_add_comment_with_illegal_args(self):
        pass

    def test_add_comment_with_string(self):
        comment = testcaserun.add_comment(self.admin_request,
                                          "{0},{1}".format(self.case_run_1.pk, self.case_run_2.pk),
                                          "Hello World!")
        self.assertIsNone(comment)

        comment = testcaserun.add_comment(self.admin_request,
                                          str(self.case_run_1.pk),
                                          "Hello World!")
        self.assertIsNone(comment)

    def test_add_comment_with_list(self):
        comment = testcaserun.add_comment(self.admin_request,
                                          [self.case_run_1.pk, self.case_run_2.pk],
                                          "Hello World!")
        self.assertIsNone(comment)

    def test_add_comment_with_int(self):
        comment = testcaserun.add_comment(self.admin_request, self.case_run_2.pk, "Hello World!")
        self.assertIsNone(comment)


class TestCaseRunAttachBug(test.TestCase):
    """Test testcaserun.attach_bug"""

    @classmethod
    def setUpClass(cls):
        super(TestCaseRunAttachBug, cls).setUpClass()
        cls.admin = UserFactory(username='update_admin', email='update_admin@example.com')
        cls.staff = UserFactory(username='update_staff', email='update_staff@example.com')
        cls.admin_request = make_http_request(user=cls.admin,
                                              user_perm='testcases.add_testcasebug')
        cls.staff_request = make_http_request(user=cls.staff)
        cls.case_run = TestCaseRunFactory()
        cls.bug_system_jira = TestCaseBugSystem.objects.get(name='JIRA')
        cls.bug_system_bz = TestCaseBugSystem.objects.get(name='Bugzilla')

    def test_attach_bug_with_no_perm(self):
        try:
            testcaserun.attach_bug(self.staff_request, {})
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_PERMS)

    @unittest.skip('TODO: not implemented yet.')
    def test_attach_bug_with_incorrect_type_value(self):
        pass

    @unittest.skip('TODO: fix code to make this test pass.')
    def test_attach_bug_with_no_required_args(self):
        try:
            testcaserun.attach_bug(self.admin_request, {
                "summary": "This is summary.",
                "description": "This is description."
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

        try:
            testcaserun.attach_bug(self.admin_request, {
                "description": "This is description."
            })
        except Fault as f:
            # FIXME: 400 is reasonable
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

        try:
            testcaserun.attach_bug(self.admin_request, {
                "summary": "This is summary.",
            })
        except Fault as f:
            # FIXME: 400 is reasonable
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

    def test_attach_bug_with_required_args(self):
        try:
            bug = testcaserun.attach_bug(self.admin_request, {
                "case_run_id": self.case_run.pk,
                "bug_id": '1',
                "bug_system_id": self.bug_system_bz.pk,
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(bug)

        try:
            bug = testcaserun.attach_bug(self.admin_request, {
                "case_run_id": self.case_run.pk,
                "bug_id": "TCMS-123",
                "bug_system_id": self.bug_system_jira.pk,
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(bug)

    def test_attach_bug_with_all_fields(self):
        try:
            bug = testcaserun.attach_bug(self.admin_request, {
                "case_run_id": self.case_run.pk,
                "bug_id": '2',
                "bug_system_id": self.bug_system_bz.pk,
                "summary": "This is summary.",
                "description": "This is description."
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(bug)

    def test_succeed_to_attach_bug_by_passing_extra_data(self):
        testcaserun.attach_bug(self.admin_request, {
            "case_run_id": self.case_run.pk,
            "bug_id": '1200',
            "bug_system_id": self.bug_system_bz.pk,
            "summary": "This is summary.",
            "description": "This is description.",
            "FFFF": "aaa"
        })
        bugs_added = self.case_run.case.case_bug.filter(
            bug_id='1200', bug_system=self.bug_system_bz.pk).count()
        self.assertEqual(1, bugs_added)

    def test_attach_bug_with_non_existing_case_run(self):
        try:
            testcaserun.attach_bug(self.admin_request, {
                "case_run_id": 111111111,
                "bug_id": '2',
                "bug_system_id": self.bug_system_bz.pk,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ILLEGAL_ARGS)

    def test_attach_bug_with_non_existing_bug_system(self):
        try:
            testcaserun.attach_bug(self.admin_request, {
                "case_run_id": self.case_run.pk,
                "bug_id": '2',
                "bug_system_id": 111111111,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ILLEGAL_ARGS)

    def test_attach_bug_with_chinese(self):
        try:
            bug = testcaserun.attach_bug(self.admin_request, {
                "case_run_id": self.case_run.pk,
                "bug_id": '12',
                "bug_system_id": self.bug_system_bz.pk,
                "summary": "你好，中国",
                "description": "中国是一个具有悠久历史的文明古国"
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(bug)


class TestCaseRunAttachLog(test.TestCase):
    """Test testcaserun.attach_log"""

    @classmethod
    def setUpClass(cls):
        super(TestCaseRunAttachLog, cls).setUpClass()
        cls.case_run = TestCaseRunFactory()

    @unittest.skip('TODO: not implemented yet.')
    def test_attach_log_with_bad_args(self):
        pass

    def test_attach_log_with_not_enough_args(self):
        try:
            testcaserun.attach_log(None, '', '')
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.XMLRPC_INTERNAL_ERROR)

        try:
            testcaserun.attach_log(None, '')
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.XMLRPC_INTERNAL_ERROR)

        try:
            testcaserun.attach_log(None)
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.XMLRPC_INTERNAL_ERROR)

        try:
            testcaserun.attach_log(None, '', '', '')
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.XMLRPC_INTERNAL_ERROR)

    def test_attach_log_with_non_exist_id(self):
        try:
            testcaserun.attach_log(None, 5523533, '', '')
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

    @unittest.skip('TODO: code should be fixed to make this test pass')
    def test_attach_log_with_invalid_url(self):
        try:
            testcaserun.attach_log(None, self.case_run.pk, "UT test logs", 'aaaaaaaaa')
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_URL_FORMAT)

    def test_attach_log(self):
        try:
            url = "http://127.0.0.1/test/test-log.log"
            log = testcaserun.attach_log(None, self.case_run.pk, "UT test logs", url)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(log)


class TestCaseRunCheckStatus(test.TestCase):
    """Test testcaserun.check_case_run_status"""

    @unittest.skip('TODO: fix code to make this test pass.')
    def test_check_status_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                testcaserun.check_case_run_status(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    @unittest.skip('TODO: fix code to make this test pass.')
    def test_check_status_with_empty_name(self):
        try:
            testcaserun.check_case_run_status(None, '')
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    @unittest.skip('TODO: fix code to make this test pass.')
    def test_check_status_with_non_basestring(self):
        bad_args = (True, False, 1, 0, -1, [1], (1,), dict(a=1), 0.7)
        for arg in bad_args:
            try:
                testcaserun.check_case_run_status(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_check_status_with_name(self):
        try:
            status = testcaserun.check_case_run_status(None, "IDLE")
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(status)
            self.assertEqual(status['id'], 1)
            self.assertEqual(status['name'], "IDLE")

    def test_check_status_with_non_exist_name(self):
        try:
            testcaserun.check_case_run_status(None, "ABCDEFG")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestCaseRunDetachBug(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCaseRunDetachBug, cls).setUpClass()
        cls.admin = UserFactory()
        cls.staff = UserFactory()
        cls.admin_request = make_http_request(user=cls.admin,
                                              user_perm='testcases.delete_testcasebug')
        cls.staff_request = make_http_request(user=cls.staff,
                                              user_perm='testcases.add_testcasebug')

        cls.bug_system_bz = TestCaseBugSystem.objects.get(name='Bugzilla')
        cls.bug_system_jira = TestCaseBugSystem.objects.get(name='JIRA')
        cls.case_run = TestCaseRunFactory()

    def setUp(self):
        self.bug_id = '67890'
        testcaserun.attach_bug(self.staff_request, {
            'case_run_id': self.case_run.pk,
            'bug_id': self.bug_id,
            'bug_system_id': self.bug_system_bz.pk,
            'summary': 'Testing TCMS',
            'description': 'Just foo and bar',
        })

        self.jira_key = 'AWSDF-112'
        testcaserun.attach_bug(self.staff_request, {
            'case_run_id': self.case_run.pk,
            'bug_id': self.jira_key,
            'bug_system_id': self.bug_system_jira.pk,
            'summary': 'Testing TCMS',
            'description': 'Just foo and bar',
        })

    def tearDown(self):
        self.case_run.case.case_bug.all().delete()

    @unittest.skip('TODO: fix get_bugs_s to make this test pass.')
    def test_detach_bug_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                testcaserun.detach_bug(self.admin_request, arg, '12345')
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.detach_bug(self.admin_request, self.case_run.pk, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_detach_bug_with_non_exist_id(self):
        original_links_count = self.case_run.case.case_bug.count()
        testcaserun.detach_bug(self.admin_request, 9999999, '123456')
        self.assertEqual(original_links_count, self.case_run.case.case_bug.count())

    @unittest.skip('Refer to #148.')
    def test_detach_bug_with_non_exist_bug(self):
        original_links_count = self.case_run.case.case_bug.count()
        nonexisting_bug = '{0}111'.format(self.bug_id)
        testcaserun.detach_bug(self.admin_request, self.case_run.pk, nonexisting_bug)
        self.assertEqual(original_links_count, self.case_run.case.case_bug.count())

    @unittest.skip('Refer to #148.')
    def test_detach_bug(self):
        testcaserun.detach_bug(self.admin_request, self.case_run.pk, self.bug_id)
        self.assertFalse(self.case_run.case.case_bug.filter(bug_id=self.bug_id).exists())

    @unittest.skip('TODO: fix get_bugs_s to make this test pass.')
    def test_detach_bug_with_illegal_args(self):
        bad_args = ("AAAA", ['A', 'B', 'C'], dict(A=1, B=2), True, False, (1, 2, 3, 4), -100)
        for arg in bad_args:
            try:
                testcaserun.detach_bug(self.admin_request, arg, self.bug_id)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ILLEGAL_ARGS)

            try:
                testcaserun.detach_bug(self.admin_request, self.case_run.pk, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ILLEGAL_ARGS)

    def test_detach_bug_with_no_perm(self):
        try:
            testcaserun.detach_bug(self.staff_request, self.case_run.pk, self.bug_id)
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_PERMS)


class TestCaseRunDetachLog(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCaseRunDetachLog, cls).setUpClass()
        cls.status_idle = TestCaseRunStatus.objects.get(name='IDLE')
        cls.tester = UserFactory()
        cls.case_run = TestCaseRunFactory(assignee=cls.tester, tested_by=None,
                                          notes='testing ...',
                                          sortkey=10,
                                          case_run_status=cls.status_idle)

    def setUp(self):
        testcaserun.attach_log(None, self.case_run.pk, 'Related issue', 'https://localhost/issue/1')
        self.link = self.case_run.links.all()[0]

    @unittest.skip('TODO: fix get_bugs_s to make this test pass.')
    def test_detach_log_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                testcaserun.detach_log(None, arg, self.link.pk)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.detach_log(None, self.case_run.pk, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_detach_log_with_not_enough_args(self):
        try:
            testcaserun.detach_log(None, '')
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.XMLRPC_INTERNAL_ERROR)

        try:
            testcaserun.detach_log(None)
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.XMLRPC_INTERNAL_ERROR)

        try:
            testcaserun.detach_log(None, '', '', '')
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.XMLRPC_INTERNAL_ERROR)

    def test_detach_log_with_non_exist_id(self):
        try:
            testcaserun.detach_log(None, 9999999, self.link.pk)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.XMLRPC_INTERNAL_ERROR)

    def test_detach_log_with_non_exist_log(self):
        testcaserun.detach_log(None, self.case_run.pk, 999999999)
        self.assertEqual(1, self.case_run.links.count())
        self.assertEqual(self.link.pk, self.case_run.links.all()[0].pk)

    @unittest.skip('TODO: fix get_bugs_s to make this test pass.')
    def test_detach_log_with_invalid_type_args(self):
        bad_args = ("", "AAA", (1,), [1], dict(a=1), True, False)
        for arg in bad_args:
            try:
                testcaserun.detach_log(None, arg, self.link.pk)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.detach_log(None, self.case_run.pk, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_detach_log(self):
        testcaserun.detach_log(None, self.case_run.pk, self.link.pk)
        self.assertEqual([], list(self.case_run.links.all()))


@unittest.skip('not implemented yet.')
class TestCaseRunFilter(TestCase):
    pass


@unittest.skip('not implemented yet.')
class TestCaseRunFilterCount(TestCase):
    pass


class TestCaseRunGet(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCaseRunGet, cls).setUpClass()
        cls.status_idle = TestCaseRunStatus.objects.get(name='IDLE')
        cls.tester = UserFactory()
        cls.case_run = TestCaseRunFactory(assignee=cls.tester, tested_by=None,
                                          notes='testing ...',
                                          sortkey=10,
                                          case_run_status=cls.status_idle)

    @unittest.skip('TODO: fix get_bugs_s to make this test pass.')
    def test_get_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                testcaserun.get(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    @unittest.skip('TODO: fix get_bugs_s to make this test pass.')
    def test_get_with_non_integer(self):
        non_integer = (True, False, '', 'aaaa', self, [1], (1,), dict(a=1), 0.7)
        for arg in non_integer:
            try:
                testcaserun.get(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_with_non_exist_id(self):
        try:
            testcaserun.get(None, 11111111)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_with_id(self):
            tcr = testcaserun.get(None, self.case_run.pk)
            self.assertIsNotNone(tcr)
            self.assertEqual(tcr['build_id'], self.case_run.build.pk)
            self.assertEqual(tcr['case_id'], self.case_run.case.pk)
            self.assertEqual(tcr['assignee_id'], self.tester.pk)
            self.assertEqual(tcr['tested_by_id'], None)
            self.assertEqual(tcr['notes'], 'testing ...')
            self.assertEqual(tcr['sortkey'], 10)
            self.assertEqual(tcr['case_run_status'], 'IDLE')
            self.assertEqual(tcr['case_run_status_id'], self.status_idle.pk)


class TestCaseRunGetSet(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCaseRunGetSet, cls).setUpClass()
        cls.status_idle = TestCaseRunStatus.objects.get(name='IDLE')
        cls.tester = UserFactory()
        cls.case_run = TestCaseRunFactory(assignee=cls.tester, tested_by=None,
                                          notes='testing ...',
                                          case_run_status=cls.status_idle)

    @unittest.skip('TODO: fix get_bugs_s to make this test pass.')
    def test_get_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            try:
                testcaserun.get_s(None, arg, self.case_run.run.pk, self.case_run.build.pk, 0)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.get_s(None, self.case_run.case.pk, arg, self.case_run.build.pk, 0)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.get_s(None, self.case_run.case.pk, self.case_run.run.pk, arg, 0)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.get_s(None,
                                  self.case_run.case.pk,
                                  self.case_run.run.pk,
                                  self.case_run.build.pk,
                                  arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_with_non_exist_run(self):
        try:
            testcaserun.get_s(None, self.case_run.case.pk, 1111111, self.case_run.build.pk, 0)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

    def test_get_with_non_exist_case(self):
        try:
            testcaserun.get_s(None, 11111111, self.case_run.run.pk, self.case_run.build.pk, 0)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

    def test_get_with_non_exist_build(self):
        try:
            testcaserun.get_s(None, self.case_run.case.pk, self.case_run.run.pk, 1111111, 0)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

    def test_get_with_non_exist_env(self):
        try:
            testcaserun.get_s(None,
                              self.case_run.case.pk,
                              self.case_run.run.pk,
                              self.case_run.build.pk,
                              999999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

    def test_get_with_no_env(self):
        tcr = testcaserun.get_s(None,
                                self.case_run.case.pk,
                                self.case_run.run.pk,
                                self.case_run.build.pk)
        self.assertIsNotNone(tcr)
        self.assertEqual(tcr['case_run_id'], self.case_run.pk)
        self.assertEqual(tcr['run_id'], self.case_run.run.pk)
        self.assertEqual(tcr['case_id'], self.case_run.case.pk)
        self.assertEqual(tcr['assignee_id'], self.tester.pk)
        self.assertEqual(tcr['tested_by_id'], None)
        self.assertEqual(tcr['build_id'], self.case_run.build.pk)
        self.assertEqual(tcr['notes'], 'testing ...')
        self.assertEqual(tcr['case_run_status_id'], self.status_idle.pk)
        self.assertEqual(tcr['environment_id'], 0)


class TestCaseRunGetBugs(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCaseRunGetBugs, cls).setUpClass()
        cls.admin = UserFactory()
        cls.admin_request = make_http_request(user=cls.admin,
                                              user_perm='testcases.add_testcasebug')

        cls.case_run = TestCaseRunFactory()
        cls.bug_system_bz = TestCaseBugSystem.objects.get(name='Bugzilla')
        testcaserun.attach_bug(cls.admin_request, {
            'case_run_id': cls.case_run.pk,
            'bug_id': '67890',
            'bug_system_id': cls.bug_system_bz.pk,
            'summary': 'Testing TCMS',
            'description': 'Just foo and bar',
        })

    def test_get_bugs_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                testcaserun.get_bugs(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    @unittest.skip('TODO: fix get_bugs to make this test pass.')
    def test_get_bugs_with_non_integer(self):
        non_integer = (True, False, '', 'aaaa', self, [1], (1,), dict(a=1), 0.7)
        for arg in non_integer:
            try:
                testcaserun.get_bugs(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_bugs_with_non_exist_id(self):
        bugs = testcaserun.get_bugs(None, 11111111)
        self.assertEqual(len(bugs), 0)
        self.assertIsInstance(bugs, list)

    def test_get_bugs_with_id(self):
        bugs = testcaserun.get_bugs(None, self.case_run.pk)
        self.assertIsNotNone(bugs)
        self.assertEqual(1, len(bugs))
        self.assertEqual(bugs[0]['summary'], 'Testing TCMS')
        self.assertEqual(bugs[0]['bug_id'], '67890')


class TestCaseRunGetBugsSet(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCaseRunGetBugsSet, cls).setUpClass()
        cls.admin = UserFactory(username='update_admin', email='update_admin@example.com')
        cls.admin_request = make_http_request(user=cls.admin,
                                              user_perm='testcases.add_testcasebug')

        cls.case_run = TestCaseRunFactory()
        cls.bug_system_bz = TestCaseBugSystem.objects.get(name='Bugzilla')
        testcaserun.attach_bug(cls.admin_request, {
            'case_run_id': cls.case_run.pk,
            'bug_id': '67890',
            'bug_system_id': cls.bug_system_bz.pk,
            'summary': 'Testing TCMS',
            'description': 'Just foo and bar',
        })

    def test_get_bug_set_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            try:
                testcaserun.get_bugs_s(None, arg, self.case_run.case.pk, self.case_run.build.pk, 0)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.get_bugs_s(None, self.case_run.run.pk, arg, self.case_run.build.pk, 0)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.get_bugs_s(None, self.case_run.run.pk, self.case_run.case.pk, arg, 0)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    @unittest.skip('TODO: fix get_bugs_s to make this test pass.')
    def test_get_bug_set_with_invalid_environment_value(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            try:
                testcaserun.get_bugs_s(None,
                                       self.case_run.run.pk,
                                       self.case_run.case.pk,
                                       self.case_run.build.pk,
                                       arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_bug_set_with_non_exist_run(self):
        tcr = testcaserun.get_bugs_s(None,
                                     1111111,
                                     self.case_run.case.pk,
                                     self.case_run.build.pk,
                                     0)
        self.assertIsNotNone(tcr)
        self.assertIsInstance(tcr, list)
        self.assertEqual(len(tcr), 0)

    def test_get_bug_set_with_non_exist_case(self):
        tcr = testcaserun.get_bugs_s(None,
                                     self.case_run.run.pk,
                                     11111111,
                                     self.case_run.build.pk,
                                     0)
        self.assertIsNotNone(tcr)
        self.assertIsInstance(tcr, list)
        self.assertEqual(len(tcr), 0)

    def test_get_bug_set_with_non_exist_build(self):
        tcr = testcaserun.get_bugs_s(None,
                                     self.case_run.run.pk,
                                     self.case_run.case.pk,
                                     1111111,
                                     0)
        self.assertIsNotNone(tcr)
        self.assertIsInstance(tcr, list)
        self.assertEqual(len(tcr), 0)

    def test_get_bug_set_with_non_exist_env(self):
        tcr = testcaserun.get_bugs_s(None,
                                     self.case_run.run.pk,
                                     self.case_run.case.pk,
                                     self.case_run.build.pk,
                                     999999)
        self.assertIsNotNone(tcr)
        self.assertIsInstance(tcr, list)
        self.assertEqual(len(tcr), 0)

    def test_get_bug_set_by_omitting_argument_environment(self):
        tcr = testcaserun.get_bugs_s(None,
                                     self.case_run.run.pk,
                                     self.case_run.case.pk,
                                     self.case_run.build.pk)
        self.assertIsNotNone(tcr)
        self.assertIsInstance(tcr, list)
        self.assertEqual(len(tcr), 1)
        self.assertEqual(tcr[0]['bug_id'], '67890')
        self.assertEqual(tcr[0]['summary'], 'Testing TCMS')


class TestCaseRunGetStatus(test.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCaseRunGetStatus, cls).setUpClass()
        cls.status_running = TestCaseRunStatus.objects.get(name='RUNNING')

    def test_get_all_status(self):
        rows = testcaserun.get_case_run_status(None)
        self.assertEqual(8, len(rows))
        names = [row['name'] for row in rows]
        self.assertTrue("IDLE" in names)
        self.assertTrue("PASSED" in names)
        self.assertTrue("FAILED" in names)
        self.assertTrue("RUNNING" in names)
        self.assertTrue("PAUSED" in names)
        self.assertTrue("BLOCKED" in names)
        self.assertTrue("ERROR" in names)
        self.assertTrue("WAIVED" in names)

        rows = testcaserun.get_case_run_status(None, None)
        self.assertEqual(8, len(rows))
        names = [row['name'] for row in rows]
        self.assertTrue("IDLE" in names)
        self.assertTrue("PASSED" in names)
        self.assertTrue("FAILED" in names)
        self.assertTrue("RUNNING" in names)
        self.assertTrue("PAUSED" in names)
        self.assertTrue("BLOCKED" in names)
        self.assertTrue("ERROR" in names)
        self.assertTrue("WAIVED" in names)

    @unittest.skip('TODO: fix method to make this test pass.')
    def test_get_status_with_no_args(self):
        bad_args = ([], {}, (), "", "AAAA", self)
        for arg in bad_args:
            try:
                testcaserun.get_case_run_status(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_status_with_non_exist_id(self):
        try:
            testcaserun.get_case_run_status(None, 999999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_status_with_id(self):
        status = testcaserun.get_case_run_status(None, self.status_running.pk)
        self.assertIsNotNone(status)
        self.assertEqual(status['id'], self.status_running.pk)
        self.assertEqual(status['name'], "RUNNING")

    def test_get_status_with_name(self):
        try:
            testcaserun.get_case_run_status(None, "PROPOSED")
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)


@unittest.skip('not implemented yet.')
class TestCaseRunGetCompletionTime(TestCase):
    pass


@unittest.skip('not implemented yet.')
class TestCaseRunGetCompletionTimeSet(TestCase):
    pass


@unittest.skip('not implemented yet.')
class TestCaseRunGetHistory(TestCase):
    def test_get_history(self):
        try:
            testcaserun.get_history(None, None)
        except Fault as f:
            self.assertEqual(f.faultCode, 501, AssertMessage.SHOULD_BE_501)
        else:
            self.fail(AssertMessage.NOT_IMPLEMENT_FUNC)


@unittest.skip('not implemented yet.')
class TestCaseRunGetHistorySet(TestCase):
    def test_get_history(self):
        try:
            testcaserun.get_history_s(None, None, None, None)
        except Fault as f:
            self.assertEqual(f.faultCode, 501, AssertMessage.SHOULD_BE_501)
        else:
            self.fail(AssertMessage.NOT_IMPLEMENT_FUNC)


class TestCaseRunGetLogs(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCaseRunGetLogs, cls).setUpClass()
        cls.case_run_1 = TestCaseRunFactory()
        cls.case_run_2 = TestCaseRunFactory()
        testcaserun.attach_log(None, cls.case_run_1.pk, "Test logs", "http://www.google.com")

    @unittest.skip('TODO: fix method to make this test pass.')
    def test_get_logs_with_no_args(self):
        bad_args = (None, [], (), {}, "")
        for arg in bad_args:
            try:
                testcaserun.get_logs(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    @unittest.skip('TODO: fix method to make this test pass.')
    def test_get_logs_with_non_integer(self):
        bad_args = (True, False, "AAA", 0.7, -1)
        for arg in bad_args:
            try:
                testcaserun.get_logs(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_logs_with_non_exist_id(self):
        try:
            testcaserun.get_logs(None, 99999999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

    def test_get_empty_logs(self):
        logs = testcaserun.get_logs(None, self.case_run_2.pk)
        self.assertIsInstance(logs, list)
        self.assertEqual(len(logs), 0)

    def test_get_logs(self):
        logs = testcaserun.get_logs(None, self.case_run_1.pk)
        self.assertIsInstance(logs, list)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['id'], 1)
        self.assertEqual(logs[0]['name'], "Test logs")
        self.assertEqual(logs[0]['url'], "http://www.google.com")


class TestCaseRunUpdate(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCaseRunUpdate, cls).setUpClass()
        cls.admin = UserFactory()
        cls.staff = UserFactory()
        cls.user = UserFactory()
        cls.admin_request = make_http_request(user=cls.admin,
                                              user_perm='testruns.change_testcaserun')
        cls.staff_request = make_http_request(user=cls.staff)

        cls.build = TestBuildFactory()
        cls.case_run_1 = TestCaseRunFactory()
        cls.case_run_2 = TestCaseRunFactory()
        cls.status_running = TestCaseRunStatus.objects.get(name='RUNNING')

    @unittest.skip('TODO: fix method to make this test pass.')
    def test_update_with_no_args(self):
        bad_args = (None, [], (), {}, "")
        for arg in bad_args:
            try:
                testcaserun.update(self.admin_request, arg, {})
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)
            try:
                testcaserun.update(self.admin_request, self.case_run_1.pk, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_single_caserun(self):
        tcr = testcaserun.update(self.admin_request, self.case_run_1.pk, {
            "build": self.build.pk,
            "assignee": self.user.pk,
            "case_run_status": self.status_running.pk,
            "notes": "AAAAAAAA",
            "sortkey": 90
        })
        self.assertIsNotNone(tcr)
        self.assertIsInstance(tcr, list)
        self.assertEqual(1, len(tcr))
        self.assertEqual(tcr[0]['build'], self.build.name)
        self.assertEqual(tcr[0]['assignee'], self.user.username)
        self.assertEqual(tcr[0]['case_run_status'], 'RUNNING')
        self.assertEqual(tcr[0]['notes'], "AAAAAAAA")
        self.assertEqual(tcr[0]['sortkey'], 90)

    def test_update_with_multi_caserun(self):
        tcr = testcaserun.update(self.admin_request,
                                 [self.case_run_1.pk, self.case_run_2.pk],
                                 {
                                     "build": self.build.pk,
                                     "assignee": self.user.pk,
                                     "case_run_status": self.status_running.pk,
                                     "notes": "Hello World!",
                                     "sortkey": 180
                                 })
        self.assertIsNotNone(tcr)
        self.assertIsInstance(tcr, list)
        self.assertEqual(len(tcr), 2)
        self.assertEqual(tcr[0]['build'], tcr[1]['build'])
        self.assertEqual(tcr[0]['assignee'], tcr[1]['assignee'])
        self.assertEqual(tcr[0]['case_run_status'], tcr[1]['case_run_status'])
        self.assertEqual(tcr[0]['notes'], tcr[1]['notes'])
        self.assertEqual(tcr[0]['sortkey'], tcr[1]['sortkey'])

    def test_update_with_non_exist_build(self):
        try:
            testcaserun.update(self.admin_request, self.case_run_1.pk, {
                "build": 1111111,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_non_exist_assignee(self):
        try:
            testcaserun.update(self.admin_request, self.case_run_1.pk, {
                "assignee": 1111111,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_non_exist_status(self):
        try:
            testcaserun.update(self.admin_request, self.case_run_1.pk, {
                "case_run_status": 1111111,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_by_ignoring_undoced_fields(self):
        case_run = testcaserun.update(self.admin_request, self.case_run_1.pk, {
            "notes": "AAAA",
            "close_date": datetime.now(),
            'anotherone': 'abc',
        })
        self.assertEqual('AAAA', case_run[0]['notes'])

    def test_update_with_no_perm(self):
        try:
            testcaserun.update(self.staff_request, self.case_run_1.pk, {
                "notes": "AAAA",
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)
