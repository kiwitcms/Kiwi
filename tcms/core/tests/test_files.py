# -*- coding: utf-8 -*-

import os
import string
import tempfile
import shutil

from mock import patch

from django.core.urlresolvers import reverse
from django.test import Client

from tcms.tests import BasePlanCase
from tcms.tests import create_request_user
from tcms.tests import user_should_have_perm
from tcms.management.models import TestAttachment
from tcms.testplans.models import TestPlanAttachment
from tcms.testcases.models import TestCaseAttachment


class TestUploadFile(BasePlanCase):
    """Test view upload_file"""

    @classmethod
    def setUpTestData(cls):
        super(TestUploadFile, cls).setUpTestData()

        cls.password = 'password'
        cls.user = create_request_user(username='uploader', password=cls.password)
        user_should_have_perm(cls.user, 'management.add_testattachment')
        user_should_have_perm(cls.user, 'testcases.add_testcaseattachment')

    @classmethod
    def setUpClass(cls):
        super(TestUploadFile, cls).setUpClass()

        cls.file_upload_dir = tempfile.mkdtemp(prefix='{0}-upload-dir'.format(cls.__name__))
        cls.upload_file_url = reverse('tcms.core.files.upload_file')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.file_upload_dir)

        super(TestUploadFile, cls).tearDownClass()

    def setUp(self):
        super(TestUploadFile, self).setUp()

        fd, self.upload_filename = tempfile.mkstemp(
            prefix='{0}-upload-file.txt'.format(self.__class__.__name__))
        os.write(fd, string.ascii_letters * 100)
        os.close(fd)

        self.client = Client()
        self.client.login(username=self.user.username, password=self.password)

    def tearDown(self):
        os.remove(self.upload_filename)
        super(TestUploadFile, self).tearDown()

    def test_no_file_is_posted(self):
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
        with open(self.upload_filename, 'r') as upload_file:
            response = self.client.post(self.upload_file_url,
                                        {'to_plan_id': self.plan.pk,
                                         'upload_file': upload_file})

        self.assertContains(response, 'You upload entity is too large')

    def test_upload_file_to_plan(self):
        with patch('tcms.core.files.settings.FILE_UPLOAD_DIR', new=self.file_upload_dir):
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
        with patch('tcms.core.files.settings.FILE_UPLOAD_DIR', new=self.file_upload_dir):
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
