# -*- coding: utf-8 -*-
from datetime import datetime
from xmlrpclib import Fault

from django.contrib.auth.models import User
from django.test import TestCase

from tcms.xmlrpc.api import testcaserun
from tcms.xmlrpc.tests.utils import make_http_request
from tcms.testruns.models import TestCaseRun


class AssertMessage(object):
    NOT_VALIDATE_ARGS = "Missing validations for args."
    NOT_VALIDATE_REQUIRED_ARGS = "Missing validations for required args."
    NOT_VALIDATE_ILLEGAL_ARGS = "Missing validations for illegal args."
    NOT_VALIDATE_FOREIGN_KEY = "Missing validations for foreign key."
    NOT_VALIDATE_LENGTH = "Missing validations for length of value."
    NOT_VALIDATE_URL_FORMAT = "Missing validations for URL format."

    SHOULD_BE_400 = "Error code should be 400."
    SHOULD_BE_409 = "Error code should be 409."
    SHOULD_BE_500 = "Error code should be 500."
    SHOULD_BE_403 = "Error code should be 403."
    SHOULD_BE_401 = "Error code should be 401."
    SHOULD_BE_404 = "Error code should be 404."
    SHOULD_BE_501 = "Error code should be 501."
    SHOULD_BE_1 = "Error code should be 1."

    UNEXCEPT_ERROR = "Unexcept error occurs."
    NEED_ENCODE_UTF8 = "Need to encode with utf8."

    NOT_IMPLEMENT_FUNC = "Not implement yet."
    XMLRPC_INTERNAL_ERROR = "xmlrpc library error."
    NOT_VALIDATE_PERMS = "Missing validations for user perms."


class TestCaseRunCreate(TestCase):

    def setUp(self):
        super(TestCaseRunCreate, self).setUp()

        self.admin = User(username='tcr_admin',
                          email='tcr_admin@example.com')
        self.staff = User(username='tcr_staff',
                          email='tcr_staff@example.com')
        self.admin.save()
        self.staff.save()
        self.admin_request = make_http_request(
            user=self.admin,
            user_perm='testruns.add_testcaserun'
        )
        self.staff_request = make_http_request(
            user=self.staff
        )

    def tearDown(self):
        super(TestCaseRunCreate, self).tearDown()

        self.admin.delete()
        self.staff.delete()

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
                "case_run_status": 1,
                "notes": "unit test 2"
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

        try:
            testcaserun.create(self.admin_request, {
                "build": 1,
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
                "run": 1,
                "build": 1,
                "assignee": self.staff.pk,
                "case_run_status": 1,
                "notes": "unit test 2"
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

    def test_create_with_illegal_fields(self):
        try:
            testcaserun.create(self.admin_request, {
                "run": 1,
                "build": 1,
                "case": 3,
                "A": 2
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ILLEGAL_ARGS)

        try:
            testcaserun.create(self.admin_request, {
                "run": 1,
                "build": 1,
                "case": 3,
                "tested_by": self.staff.pk
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ILLEGAL_ARGS)

    def test_create_with_required_fields(self):
        try:
            tcr = testcaserun.create(self.admin_request, {
                "run": 1,
                "build": 1,
                "case": 3,
                "case_text_version": 15
            })
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(tcr)
            self.assertEquals(tcr['build_id'], 1)
            self.assertEquals(tcr['case_id'], 3)
            self.assertEquals(tcr['run_id'], 1)

    def test_create_with_all_fields(self):
        try:
            tcr = testcaserun.create(self.admin_request, {
                "run": 1,
                "build": 1,
                "case": 3,
                "assignee": 1,
                "notes": "test_create_with_all_fields",
                "sortkey": 90,
                "case_run_status": 4,
                "case_text_version": 3,
            })
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(tcr)
            self.assertEquals(tcr['build_id'], 1)
            self.assertEquals(tcr['case_id'], 3)
            self.assertEquals(tcr['assignee_id'], 1)
            self.assertEquals(tcr['notes'], "test_create_with_all_fields")
            self.assertEquals(tcr['sortkey'], 90)
            self.assertEquals(tcr['case_run_status'], 'RUNNING')

    def test_create_with_non_exist_fields(self):
        try:
            testcaserun.create(self.admin_request, {
                "run": 1,
                "build": 1,
                "case": 111111,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_FOREIGN_KEY)

        try:
            testcaserun.create(self.admin_request, {
                "run": 11111,
                "build": 1,
                "case": 1,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_FOREIGN_KEY)

        try:
            testcaserun.create(self.admin_request, {
                "run": 1,
                "build": 11222222,
                "case": 1,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_FOREIGN_KEY)

    def test_create_with_chinese(self):
        try:
            tcr = testcaserun.create(self.admin_request, {
                "run": 1,
                "build": 1,
                "case": 3,
                "notes": "开源中国",
                "case_text_version": 13
            })
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.NEED_ENCODE_UTF8)
        else:
            self.assertIsNotNone(tcr)
            self.assertEquals(tcr['build_id'], 1)
            self.assertEquals(tcr['case_id'], 3)
            self.assertEquals(tcr['assignee_id'], 1)
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

        try:
            testcaserun.create(self.admin_request, {
                "run": 1,
                "build": 1,
                "case": 111111,
                "notes": large_str
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_LENGTH)

    def test_create_with_no_perm(self):
        try:
            testcaserun.create(self.staff_request, {
                "run": 1,
                "build": 1,
                "case": 3,
                "assignee": 1,
                "notes": "test_create_with_all_fields",
                "sortkey": 90,
                "case_run_status": 4,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_PERMS)


class TestCaseRunAddComment(TestCase):

    def setUp(self):
        super(TestCaseRunAddComment, self).setUp()
        self.admin = User(username='update_admin',
                          email='update_admin@example.com')
        self.admin.save()
        self.admin_request = make_http_request(
            user=self.admin,
            user_perm='testruns.change_testcaserun'
        )

    def tearDown(self):
        super(TestCaseRunAddComment, self).tearDown()
        self.admin.delete()

    def test_add_comment_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                testcaserun.add_comment(self.admin_request, arg, "Hello World!")
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.add_comment(self.admin_request, 1, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_add_comment_with_illegal_args(self):
        bad_args = ("", "AA", "1@2", "1!2", "1.2", (1, 2), dict(a=1, b=2),
                    True, False, self)
        for arg in bad_args:
            try:
                testcaserun.add_comment(self.admin_request, arg, "Hello World!")
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        bad_args = (1, True, False, -1, 0, (1,), [1], dict(a=1), list)
        for arg in bad_args:
            try:
                testcaserun.add_comment(self.admin_request, 1, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_add_comment_with_string(self):
        try:
            comment = testcaserun.add_comment(self.admin_request, "1,2",
                                              "Hello World!")
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(comment)

        try:
            comment = testcaserun.add_comment(self.admin_request, "1",
                                              "Hello World!")
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(comment)

    def test_add_comment_with_list(self):
        try:
            comment = testcaserun.add_comment(self.admin_request, [1, 2],
                                              "Hello World!")
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(comment)

    def test_add_comment_with_int(self):
        try:
            comment = testcaserun.add_comment(self.admin_request, 1,
                                              "Hello World!")
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(comment)


class TestCaseRunAttachBug(TestCase):

    def setUp(self):
        super(TestCaseRunAttachBug, self).setUp()
        self.admin = User(username='update_admin',
                          email='update_admin@example.com')
        self.admin.save()
        self.staff = User(username='update_staff',
                          email='update_staff@example.com')
        self.staff.save()
        self.admin_request = make_http_request(
            user=self.admin,
            user_perm='testcases.add_testcasebug'
        )
        self.staff_request = make_http_request(
            user=self.staff
        )

    def tearDown(self):
        super(TestCaseRunAttachBug, self).tearDown()
        self.admin.delete()
        self.staff.delete()

    def test_attach_bug_with_no_perm(self):
        try:
            testcaserun.attach_bug(self.staff_request, {})
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_PERMS)

    def test_attach_bug_with_no_args(self):
        bad_args = (None, [], {}, (), 1, 0, -1, True, False, '', 'aaaa', object)
        for arg in bad_args:
            try:
                testcaserun.attach_bug(self.admin_request, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

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
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

        try:
            testcaserun.attach_bug(self.admin_request, {
                "summary": "This is summary.",
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

    def test_attach_bug_with_required_args(self):
        try:
            bug = testcaserun.attach_bug(self.admin_request, {
                "case_run_id": 1,
                "bug_id": 1,
                "bug_system_id": 1,
            })
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(bug)

        try:
            bug = testcaserun.attach_bug(self.admin_request, {
                "case_run_id": 1,
                "bug_id": "TCMS-123",
                "bug_system_id": 2,
            })
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(bug)

    def test_attach_bug_with_all_fields(self):
        try:
            bug = testcaserun.attach_bug(self.admin_request, {
                "case_run_id": 1,
                "bug_id": 2,
                "bug_system_id": 1,
                "summary": "This is summary.",
                "description": "This is description."
            })
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(bug)

    def test_attach_bug_with_illegal_fields(self):
        try:
            testcaserun.attach_bug(self.admin_request, {
                "case_run_id": 1,
                "bug_id": 2,
                "bug_system_id": 1,
                "summary": "This is summary.",
                "description": "This is description.",
                "FFFF": "aaa"
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ILLEGAL_ARGS)

        try:
            testcaserun.attach_bug(self.admin_request, {
                "case_run_id": 1,
                "bug_id": 2,
                "bug_system_id": 1,
                "summary": "This is summary.",
                "description": "This is description.",
                "case_id": 1
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ILLEGAL_ARGS)

    def test_attach_bug_with_non_exist_fields(self):
        try:
            testcaserun.attach_bug(self.admin_request, {
                "case_run_id": 111111111,
                "bug_id": 2,
                "bug_system_id": 1,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ILLEGAL_ARGS)

        try:
            testcaserun.attach_bug(self.admin_request, {
                "case_run_id": 1,
                "bug_id": 2,
                "bug_system_id": 111111111,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ILLEGAL_ARGS)

    def test_attach_bug_with_chinese(self):
        try:
            bug = testcaserun.attach_bug(self.admin_request, {
                "case_run_id": 1,
                "bug_id": 12,
                "bug_system_id": 1,
                "summary": "This is summary.",
                "description": "开源中国"
            })
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(bug)

        try:
            bug = testcaserun.attach_bug(self.admin_request, {
                "case_run_id": 1,
                "bug_id": 33,
                "bug_system_id": 1,
                "summary": "开源中国",
                "description": "This is description."
            })
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(bug)

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

        try:
            bug = testcaserun.attach_bug(self.admin_request, {
                "case_run_id": 1,
                "bug_id": 2,
                "bug_system_id": 1,
                "summary": "This is summary.",
                "description": large_str
            })
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(bug)

        try:
            testcaserun.attach_bug(self.admin_request, {
                "case_run_id": 1,
                "bug_id": 2,
                "bug_system_id": 1,
                "summary": large_str,
                "description": "This is description.",
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_LENGTH)

        try:
            testcaserun.attach_bug(self.admin_request, {
                "case_run_id": 1,
                "bug_id": 2,
                "bug_system_id": 1,
                "summary": large_str,
                "description": large_str,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_LENGTH)


class TestCaseRunAttachLog(TestCase):

    def test_attach_log_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            try:
                testcaserun.attach_log(None, arg, '', '')
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.attach_log(None, 1, arg, '')
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.attach_log(None, 1, '', arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

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

    def test_attach_log_with_long_name(self):
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
        try:
            testcaserun.attach_log(None, 1, large_str, '')
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_LENGTH)

    def test_attach_log_with_invalid_url(self):
        try:
            testcaserun.attach_log(None, 1, "UT test logs", 'aaaaaaaaa')
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_URL_FORMAT)

    def test_attach_log(self):
        try:
            url = "http://127.0.0.1/test/test-log.log"
            log = testcaserun.attach_log(None, 1, "UT test logs", url)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(log)


class TestCaseRunCheckStatus(TestCase):

    def test_check_status_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                testcaserun.check_case_run_status(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_check_status_with_empty_name(self):
        try:
            testcaserun.check_case_run_status(None, '')
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

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
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(status)
            self.assertEqual(status['id'], 1)
            self.assertEqual(status['name'], "IDLE")
            self.assertIsNone(status['description'])

    def test_check_status_with_non_exist_name(self):
        try:
            testcaserun.check_case_run_status(None, "ABCDEFG")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestCaseRunDetachBug(TestCase):

    def setUp(self):
        super(TestCaseRunDetachBug, self).setUp()
        self.admin = User(username='update_admin',
                          email='update_admin@example.com')
        self.admin.save()
        self.staff = User(username='update_staff',
                          email='update_staff@example.com')
        self.staff.save()
        self.admin_request = make_http_request(
            user=self.admin,
            user_perm='testcases.delete_testcasebug'
        )
        self.staff_request = make_http_request(
            user=self.staff,
            user_perm='testcases.add_testcasebug'
        )

        testcaserun.attach_bug(self.staff_request, {
            'case_run_id': 1,
            'bug_id': 67890,
            'bug_system_id': 1,
            'summary': 'Testing TCMS',
            'description': 'Just foo and bar',
        })

        testcaserun.attach_bug(self.staff_request, {
            'case_run_id': 1,
            'bug_id': 'AWSDF-112',
            'bug_system_id': 2,
            'summary': 'Testing TCMS',
            'description': 'Just foo and bar',
        })

    def tearDown(self):
        super(TestCaseRunDetachBug, self).tearDown()
        self.admin.delete()
        self.staff.delete()

    def test_detach_bug_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                testcaserun.detach_bug(self.admin_request, arg, 1)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.detach_bug(self.admin_request, 1, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_detach_bug_with_non_exist_id(self):
        try:
            bug = testcaserun.detach_bug(self.admin_request, 9999999, 123456)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(bug)

    def test_detach_bug_with_non_exist_bug(self):
        try:
            bug = testcaserun.detach_bug(self.admin_request, 1, 654321)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(bug)

    def test_detach_bug(self):
        try:
            bug = testcaserun.detach_bug(self.admin_request, 1, 67890)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(bug)

        try:
            bug = testcaserun.detach_bug(self.admin_request, 1, "AWSDF-112")
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(bug)

    def test_detach_bug_with_illegal_args(self):
        bad_args = (
            "AAAA",
            ['A', 'B', 'C'],
            dict(A=1, B=2),
            True,
            False,
            (1, 2, 3, 4),
            -100
        )
        for arg in bad_args:
            try:
                testcaserun.detach_bug(self.admin_request, arg, 67890)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ILLEGAL_ARGS)

            try:
                testcaserun.detach_bug(self.admin_request, 1, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ILLEGAL_ARGS)

    def test_detach_bug_with_no_perm(self):
        try:
            testcaserun.detach_bug(self.staff_request, 1, 67890)
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_PERMS)


class TestCaseRunDetachLog(TestCase):

    def test_detach_log_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                testcaserun.detach_log(None, arg, 1)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.detach_log(None, 1, arg)
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
            testcaserun.detach_log(None, 9999999, 1)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.XMLRPC_INTERNAL_ERROR)

    def test_detach_log_with_non_exist_log(self):
        try:
            testcaserun.detach_log(None, 1, 999999999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.XMLRPC_INTERNAL_ERROR)

    def test_detach_log_with_invalid_type_args(self):
        bad_args = ("", "AAA", (1,), [1], dict(a=1), True, False)
        for arg in bad_args:
            try:
                testcaserun.detach_log(None, arg, 1)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.detach_log(None, 1, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_detach_log(self):
        try:
            log = testcaserun.detach_log(None, 1, 1)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNone(log)


class TestCaseRunFilter(TestCase):
    pass


class TestCaseRunFilterCount(TestCase):
    pass


class TestCaseRunGet(TestCase):

    def test_get_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                testcaserun.get(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

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
        try:
            tcr = testcaserun.get(None, 1)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(tcr)
            self.assertEquals(tcr['build_id'], 6)
            self.assertEquals(tcr['case_id'], 1)
            self.assertEquals(tcr['assignee_id'], 1)
            self.assertEquals(tcr['tested_by_id'], None)
            self.assertIsNone(tcr['notes'])
            self.assertEquals(tcr['sortkey'], 10)
            self.assertEquals(tcr['case_run_status'], 'IDLE')


class TestCaseRunGetSet(TestCase):

    def test_get_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            try:
                testcaserun.get_s(None, arg, 1, 6, 0)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.get_s(None, 1, arg, 6, 0)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.get_s(None, 1, 1, arg, 0)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.get_s(None, 1, 1, 6, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_with_non_exist_run(self):
        try:
            testcaserun.get_s(None, 1, 1111111, 6, 0)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

    def test_get_with_non_exist_case(self):
        try:
            testcaserun.get_s(None, 11111111, 1, 6, 0)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

    def test_get_with_non_exist_build(self):
        try:
            testcaserun.get_s(None, 1, 1, 1111111, 0)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

    def test_get_with_non_exist_env(self):
        try:
            testcaserun.get_s(None, 1, 1, 6, 999999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_REQUIRED_ARGS)

    def test_get_with_no_env(self):
        try:
            tcr = testcaserun.get_s(None, 1, 1, 6)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(tcr)
            self.assertEqual(tcr['case_run_id'], 1)
            self.assertEqual(tcr['run_id'], 1)
            self.assertEqual(tcr['case_id'], 1)
            self.assertEqual(tcr['assignee_id'], 1)
            self.assertEqual(tcr['tested_by_id'], None)
            self.assertEqual(tcr['build_id'], 6)
            self.assertEqual(tcr['notes'], None)
            self.assertEqual(tcr['case_run_status_id'], 1)
            self.assertEqual(tcr['environment_id'], 0)


class TestCaseRunGetBugs(TestCase):

    def setUp(self):
        super(TestCaseRunGetBugs, self).setUp()
        self.admin = User(username='update_admin',
                          email='update_admin@example.com')
        self.admin.save()
        self.admin_request = make_http_request(
            user=self.admin,
            user_perm='testcases.add_testcasebug'
        )

        testcaserun.attach_bug(self.admin_request, {
            'case_run_id': 1,
            'bug_id': 67890,
            'bug_system_id': 1,
            'summary': 'Testing TCMS',
            'description': 'Just foo and bar',
        })

    def tearDown(self):
        super(TestCaseRunGetBugs, self).tearDown()
        self.admin.delete()

    def test_get_bugs_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                testcaserun.get_bugs(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

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
        try:
            bugs = testcaserun.get_bugs(None, 11111111)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(len(bugs), 0)
            self.assertIsInstance(bugs, list)

    def test_get_bugs_with_id(self):
        try:
            bugs = testcaserun.get_bugs(None, 1)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(bugs)
            self.assertEqual(len(bugs), 1)
            self.assertEqual(bugs[0]['summary'], 'Testing TCMS')
            self.assertEqual(bugs[0]['bug_id'], '67890')


class TestCaseRunGetBugsSet(TestCase):

    def setUp(self):
        super(TestCaseRunGetBugsSet, self).setUp()
        self.admin = User(username='update_admin',
                          email='update_admin@example.com')
        self.admin.save()
        self.admin_request = make_http_request(
            user=self.admin,
            user_perm='testcases.add_testcasebug'
        )

        testcaserun.attach_bug(self.admin_request, {
            'case_run_id': 1,
            'bug_id': 67890,
            'bug_system_id': 1,
            'summary': 'Testing TCMS',
            'description': 'Just foo and bar',
        })

    def tearDown(self):
        super(TestCaseRunGetBugsSet, self).tearDown()
        self.admin.delete()

    def test_get_bug_set_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            try:
                testcaserun.get_bugs_s(None, arg, 1, 1, 0)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.get_bugs_s(None, 1, arg, 1, 0)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.get_bugs_s(None, 1, 1, arg, 0)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaserun.get_bugs_s(None, 1, 1, 1, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_bug_set_with_non_exist_run(self):
        try:
            tcr = testcaserun.get_bugs_s(None, 1111111, 1, 6, 0)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(tcr)
            self.assertIsInstance(tcr, list)
            self.assertEqual(len(tcr), 0)

    def test_get_bug_set_with_non_exist_case(self):
        try:
            tcr = testcaserun.get_bugs_s(None, 1, 11111111, 6, 0)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(tcr)
            self.assertIsInstance(tcr, list)
            self.assertEqual(len(tcr), 0)

    def test_get_bug_set_with_non_exist_build(self):
        try:
            tcr = testcaserun.get_bugs_s(None, 1, 1, 1111111, 0)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(tcr)
            self.assertIsInstance(tcr, list)
            self.assertEqual(len(tcr), 0)

    def test_get_bug_set_with_non_exist_env(self):
        try:
            tcr = testcaserun.get_bugs_s(None, 1, 1, 6, 999999)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(tcr)
            self.assertIsInstance(tcr, list)
            self.assertEqual(len(tcr), 0)

    def test_get_bug_set_with_no_env(self):
        try:
            tcr = testcaserun.get_bugs_s(None, 1, 1, 6)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(tcr)
            self.assertIsInstance(tcr, list)
            self.assertEqual(len(tcr), 1)
            self.assertEqual(tcr[0]['bug_id'], '67890')
            self.assertEqual(tcr[0]['summary'], 'Testing TCMS')


class TestCaseRunGetStatus(TestCase):

    def test_get_all_status(self):
        try:
            rows = testcaserun.get_case_run_status(None)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(8, len(rows))
            names = (row['name'] for row in rows)
            self.assertTrue("IDLE" in names)
            self.assertTrue("PASSED" in names)
            self.assertTrue("FAILED" in names)
            self.assertTrue("RUNNING" in names)
            self.assertTrue("PAUSED" in names)
            self.assertTrue("BLOCKED" in names)
            self.assertTrue("ERROR" in names)
            self.assertTrue("WAIVED" in names)

        try:
            rows = testcaserun.get_case_run_status(None, None)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(8, len(rows))
            names = (row['name'] for row in rows)
            self.assertTrue("IDLE" in names)
            self.assertTrue("PASSED" in names)
            self.assertTrue("FAILED" in names)
            self.assertTrue("RUNNING" in names)
            self.assertTrue("PAUSED" in names)
            self.assertTrue("BLOCKED" in names)
            self.assertTrue("ERROR" in names)
            self.assertTrue("WAIVED" in names)

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
        try:
            status = testcaserun.get_case_run_status(None, 1)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(status)
            self.assertEqual(status['id'], 1)
            self.assertEqual(status['name'], "IDLE")
            self.assertIsNone(status['description'])

    def test_get_status_with_name(self):
        try:
            testcaserun.get_case_run_status(None, "PROPOSED")
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestCaseRunGetCompletionTime(TestCase):
    pass


class TestCaseRunGetCompletionTimeSet(TestCase):
    pass


class TestCaseRunGetHistory(TestCase):
    def test_get_history(self):
        try:
            testcaserun.get_history(None, None)
        except Fault as f:
            self.assertEqual(f.faultCode, 501, AssertMessage.SHOULD_BE_501)
        else:
            self.fail(AssertMessage.NOT_IMPLEMENT_FUNC)


class TestCaseRunGetHistorySet(TestCase):
    def test_get_history(self):
        try:
            testcaserun.get_history_s(None, None, None, None)
        except Fault as f:
            self.assertEqual(f.faultCode, 501, AssertMessage.SHOULD_BE_501)
        else:
            self.fail(AssertMessage.NOT_IMPLEMENT_FUNC)


class TestCaseRunGetLogs(TestCase):

    def setUp(self):
        super(TestCaseRunGetLogs, self).setUp()
        testcaserun.attach_log(None, 10, "Test logs", "http://www.google.com")

    def tearDown(self):
        super(TestCaseRunGetLogs, self).tearDown()
        testcaserun.detach_log(None, 10, 1)

    def test_get_logs_with_no_args(self):
        bad_args = (None, [], (), {}, "")
        for arg in bad_args:
            try:
                testcaserun.get_logs(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

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
        try:
            logs = testcaserun.get_logs(None, 4)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsInstance(logs, list)
            self.assertEqual(len(logs), 0)

    def test_get_logs(self):
        try:
            logs = testcaserun.get_logs(None, 10)
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsInstance(logs, list)
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0]['id'], 1)
            self.assertEqual(logs[0]['name'], "Test logs")
            self.assertEqual(logs[0]['url'], "http://www.google.com")


class TestCaseRunUpdate(TestCase):

    def setUp(self):
        super(TestCaseRunUpdate, self).setUp()
        self.admin = User(username='update_admin',
                          email='update_admin@example.com')
        self.admin.save()
        self.staff = User(username='update_staff',
                          email='update_staff@example.com')
        self.staff.save()
        self.admin_request = make_http_request(
            user=self.admin,
            user_perm='testruns.change_testcaserun'
        )
        self.staff_request = make_http_request(
            user=self.staff
        )

        self.caserun = TestCaseRun(assignee=self.admin,
                                   tested_by=self.admin,
                                   case_text_version=0,
                                   running_date=datetime.now(),
                                   close_date=None,
                                   notes="setUp created.",
                                   sortkey=10,
                                   environment_id=15,
                                   case_run_status_id=1,
                                   build_id=1,
                                   case_id=1,
                                   run_id=1)
        self.caserun.save()

        self.cr2 = TestCaseRun(assignee=self.staff,
                               tested_by=self.staff,
                               case_text_version=3,
                               running_date=datetime.now(),
                               close_date=None,
                               notes="AAAAAAAAAAAAAAAAAAAAAA",
                               sortkey=30,
                               environment_id=15,
                               case_run_status_id=5,
                               build_id=3,
                               case_id=1,
                               run_id=1)
        self.cr2.save()

    def tearDown(self):
        super(TestCaseRunUpdate, self).tearDown()
        self.caserun.delete()
        self.admin.delete()
        self.staff.delete()

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
                testcaserun.update(self.admin_request, self.caserun.pk, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_single_caserun(self):
        try:
            tcr = testcaserun.update(self.admin_request, self.caserun.pk, {
                "build": 1,
                "assignee": self.staff.pk,
                "case_run_status": 2,
                "notes": "AAAAAAAA",
                "sortkey": 90
            })
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(tcr)
            self.assertIsInstance(tcr, list)
            self.assertEqual(len(tcr), 1)
            self.assertEqual(tcr[0]['build'], 'unspecified')
            self.assertEqual(tcr[0]['assignee'], self.staff.username)
            self.assertEqual(tcr[0]['case_run_status'], 'PASSED')
            self.assertEqual(tcr[0]['notes'], "AAAAAAAA")
            self.assertEqual(tcr[0]['sortkey'], 90)

    def test_update_with_multi_caserun(self):
        try:
            tcr = testcaserun.update(self.admin_request,
                                     [self.caserun.pk, self.cr2.pk],
                                     {
                                         "build": 2,
                                         "assignee": self.staff.pk,
                                         "case_run_status": 3,
                                         "notes": "Hello World!",
                                         "sortkey": 180
                                     })
        except Fault as f:
            print str(f.faultString)
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(tcr)
            self.assertIsInstance(tcr, list)
            self.assertEqual(len(tcr), 2)
            self.assertEqual(tcr[0]['build'], tcr[1]['build'])
            self.assertEqual(tcr[0]['assignee'], tcr[1]['assignee'])
            self.assertEqual(tcr[0]['case_run_status'],
                             tcr[1]['case_run_status'])
            self.assertEqual(tcr[0]['notes'], tcr[1]['notes'])
            self.assertEqual(tcr[0]['sortkey'], tcr[1]['sortkey'])

    def test_update_with_non_exist_build(self):
        try:
            testcaserun.update(self.admin_request, self.caserun.pk, {
                "build": 1111111,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_non_exist_assignee(self):
        try:
            testcaserun.update(self.admin_request, self.caserun.pk, {
                "assignee": 1111111,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_non_exist_status(self):
        try:
            testcaserun.update(self.admin_request, self.caserun.pk, {
                "case_run_status": 1111111,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_illegal_fields(self):
        try:
            testcaserun.update(self.admin_request, self.caserun.pk, {
                "notes": "AAAA",
                "B": "B"
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_undoc_fields(self):
        try:
            testcaserun.update(self.admin_request, self.caserun.pk, {
                "notes": "AAAA",
                "close_date": datetime.now()
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_no_perm(self):
        try:
            testcaserun.update(self.staff_request, self.caserun.pk, {
                "notes": "AAAA",
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)
