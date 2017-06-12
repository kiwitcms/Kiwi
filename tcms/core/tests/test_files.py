# -*- coding: utf-8 -*-

import json
import os
import shutil
import tempfile

from mock import patch

from django.core.urlresolvers import reverse
from django.test import RequestFactory

from tcms.core.files import able_to_delete_attachment
from tcms.management.models import TestAttachment
from tcms.testcases.models import TestCaseAttachment
from tcms.testplans.models import TestPlanAttachment
from tcms.tests.factories import TestAttachmentFactory
from tcms.tests.factories import TestPlanAttachmentFactory
from tcms.tests.factories import TestCaseAttachmentFactory
from tcms.tests.factories import UserFactory
from tcms.tests import BasePlanCase
from tcms.tests import create_request_user
from tcms.tests import user_should_have_perm


class TestUploadFile(BasePlanCase):
    """Test view upload_file"""

    @classmethod
    def setUpTestData(cls):
        super(TestUploadFile, cls).setUpTestData()

        cls.upload_file_url = reverse('tcms.core.files.upload_file')

        cls.password = 'password'
        cls.user = create_request_user(username='uploader', password=cls.password)
        user_should_have_perm(cls.user, 'management.add_testattachment')
        user_should_have_perm(cls.user, 'testcases.add_testcaseattachment')

    @classmethod
    def setUpClass(cls):
        super(TestUploadFile, cls).setUpClass()

        cls.file_upload_dir = tempfile.mkdtemp(
            prefix='{0}-upload-dir'.format(cls.__name__))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.file_upload_dir)

        super(TestUploadFile, cls).tearDownClass()

    def setUp(self):
        super(TestUploadFile, self).setUp()

        fd, self.upload_filename = tempfile.mkstemp(
            prefix='{0}-upload-file.txt'.format(self.__class__.__name__))
        os.write(fd, 'abc' * 100)
        os.close(fd)

    def tearDown(self):
        os.remove(self.upload_filename)
        super(TestUploadFile, self).tearDown()

    def test_no_file_is_posted(self):
        self.client.login(username=self.user.username, password=self.password)

        response = self.client.post(reverse('tcms.core.files.upload_file'),
                                    {'to_plan_id': self.plan.pk})
        self.assertRedirects(
            response,
            reverse('tcms.testplans.views.attachment', args=[self.plan.pk]))

        response = self.client.post(reverse('tcms.core.files.upload_file'),
                                    {'to_case_id': self.case_1.pk})
        self.assertRedirects(
            response,
            reverse('tcms.testcases.views.attachment', args=[self.case_1.pk]))

    @patch('tcms.core.files.settings.MAX_UPLOAD_SIZE', new=10)
    def test_refuse_if_file_is_too_big(self):
        self.client.login(username=self.user.username, password=self.password)

        with open(self.upload_filename, 'r') as upload_file:
            response = self.client.post(self.upload_file_url,
                                        {'to_plan_id': self.plan.pk,
                                         'upload_file': upload_file})

        self.assertContains(response, 'You upload entity is too large')

    def test_upload_file_to_plan(self):
        self.client.login(username=self.user.username, password=self.password)

        with patch('tcms.core.files.settings.FILE_UPLOAD_DIR',
                   new=self.file_upload_dir):
            with open(self.upload_filename, 'r') as upload_file:
                response = self.client.post(self.upload_file_url,
                                            {'to_plan_id': self.plan.pk,
                                             'upload_file': upload_file})

        self.assertRedirects(
            response,
            reverse('tcms.testplans.views.attachment', args=[self.plan.pk]))

        attachments = list(TestAttachment.objects.filter(
            file_name=os.path.basename(self.upload_filename)))
        self.assertTrue(attachments)

        attachment = attachments[0]
        self.assertEqual(self.user.pk, attachment.submitter.pk)

        plan_attachment_rel_exists = TestPlanAttachment.objects.filter(
            plan=self.plan, attachment=attachment).exists()
        self.assertTrue(plan_attachment_rel_exists)

    def test_upload_file_to_case(self):
        self.client.login(username=self.user.username, password=self.password)

        with patch('tcms.core.files.settings.FILE_UPLOAD_DIR',
                   new=self.file_upload_dir):
            with open(self.upload_filename, 'r') as upload_file:
                response = self.client.post(self.upload_file_url,
                                            {'to_case_id': self.case_1.pk,
                                             'upload_file': upload_file})

        self.assertRedirects(
            response,
            reverse('tcms.testcases.views.attachment', args=[self.case_1.pk]))

        attachments = list(TestAttachment.objects.filter(
            file_name=os.path.basename(self.upload_filename)))
        self.assertTrue(attachments)

        attachment = attachments[0]
        self.assertEqual(self.user.pk, attachment.submitter.pk)

        case_attachment_rel_exists = TestCaseAttachment.objects.filter(
            case=self.case_1, attachment=attachment).exists()
        self.assertTrue(case_attachment_rel_exists)


class TestAbleToDeleteFile(BasePlanCase):

    @classmethod
    def setUpClass(cls):
        super(TestAbleToDeleteFile, cls).setUpClass()

        cls.superuser = UserFactory(username='admin')
        cls.superuser.is_superuser = True
        cls.superuser.set_password('admin')
        cls.superuser.save()

        cls.anyone_else = UserFactory()

        cls.attachment = TestAttachmentFactory()

    def setUp(self):
        super(TestAbleToDeleteFile, self).setUp()

        self.fake_file_id = 1
        self.request = RequestFactory()

    def test_superuser_can(self):
        request = self.request.get(reverse('tcms.core.files.delete_file',
                                           args=[self.fake_file_id]))
        request.user = self.superuser
        self.assertTrue(able_to_delete_attachment(request, self.fake_file_id))

    def test_attachment_submitter_can(self):
        request = self.request.get(reverse('tcms.core.files.delete_file',
                                           args=[self.fake_file_id]))
        request.user = self.attachment.submitter
        self.assertTrue(able_to_delete_attachment(request, self.fake_file_id))

    def test_plan_author_can(self):
        request = self.request.get(reverse('tcms.core.files.delete_file',
                                           args=[self.fake_file_id]),
                                   data={'from_plan': self.plan.pk})
        request.user = self.plan.author
        self.assertTrue(able_to_delete_attachment(request, self.fake_file_id))

    def test_plan_owner_can(self):
        request = self.request.get(reverse('tcms.core.files.delete_file',
                                           args=[self.fake_file_id]),
                                   data={'from_plan': self.plan.pk})
        request.user = self.plan.owner
        self.assertTrue(able_to_delete_attachment(request, self.fake_file_id))

    def test_case_owner_can(self):
        request = self.request.get(reverse('tcms.core.files.delete_file',
                                           args=[self.fake_file_id]),
                                   data={'from_case': self.case_1.pk})
        request.user = self.case_1.author
        self.assertTrue(able_to_delete_attachment(request, self.fake_file_id))

    def test_cannot_delete_by_others(self):
        request = self.request.get(reverse('tcms.core.files.delete_file',
                                           args=[self.fake_file_id]),
                                   data={'from_case': self.case_1.pk})
        request.user = self.anyone_else
        self.assertFalse(able_to_delete_attachment(request, self.fake_file_id))


class TestDeleteFileAuthorization(BasePlanCase):

    @classmethod
    def setUpClass(cls):
        super(TestDeleteFileAuthorization, cls).setUpClass()

        cls.superuser = UserFactory(username='admin')
        cls.superuser.set_password('admin')
        cls.superuser.save()

        cls.anyone_else = UserFactory()
        cls.anyone_else_pwd = 'anyone'
        cls.anyone_else.set_password(cls.anyone_else_pwd)
        cls.anyone_else.save()

        cls.plan_attachment = TestAttachmentFactory()
        cls.plan_attachment_rel = TestPlanAttachmentFactory(
            plan=cls.plan,
            attachment=cls.plan_attachment)
        cls.submitter_pwd = 'secret'
        cls.plan_attachment.submitter.set_password(cls.submitter_pwd)
        cls.plan_attachment.submitter.save()

        cls.case_attachment = TestAttachmentFactory()
        cls.case_attachment_rel = TestCaseAttachmentFactory(
            case=cls.case_1,
            attachment=cls.case_attachment)
        cls.case_attachment.submitter.set_password(cls.submitter_pwd)
        cls.case_attachment.submitter.save()

    def test_refuse_if_user_cannot_delete_file(self):
        self.client.login(username=self.anyone_else.username,
                          password=self.anyone_else_pwd)

        url = reverse('tcms.core.files.delete_file', args=[self.plan_attachment.pk])
        response = self.client.get(url, {'from_plan': self.plan.pk})

        self.assertEqual({'rc': 2, 'response': 'auth_failure'}, json.loads(response.content))

    def test_delete_attachment_from_plan(self):
        self.client.login(username=self.plan_attachment.submitter.username,
                          password=self.submitter_pwd)

        url = reverse('tcms.core.files.delete_file', args=[self.plan_attachment.pk])
        response = self.client.get(url, {'from_plan': self.plan.pk})

        self.assertEqual({'rc': 0, 'response': 'ok'}, json.loads(response.content))
        still_has = self.plan.attachment.filter(pk=self.plan_attachment.pk).exists()
        self.assertFalse(still_has)
        # TODO: skip because delete_file does not delete a TestAttachment object from database
        # self.assertFalse(TestAttachment.objects.filter(pk=self.plan_attachment.pk).exists())

    def test_delete_attachment_from_case(self):
        self.client.login(username=self.case_attachment.submitter.username,
                          password=self.submitter_pwd)

        url = reverse('tcms.core.files.delete_file', args=[self.case_attachment.pk])
        response = self.client.get(url, {'from_case': self.case_1.pk})

        self.assertEqual({'rc': 0, 'response': 'ok'}, json.loads(response.content))
        still_has = self.case_1.attachment.filter(pk=self.case_attachment.pk).exists()
        self.assertFalse(still_has)
        # TODO: skip because delete_file does not delete a TestAttachment object from database
        # self.assertFalse(TestAttachment.objects.filter(pk=self.case_attachment.pk).exists())
