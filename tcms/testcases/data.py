# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from django_comments.models import Comment

from tcms.core.logs.models import TCMSLogModel
from tcms.testcases.models import TestCase
from tcms.testruns.models import TestCaseRun


class TestCaseViewDataMixin(object):
    """Mixin class to get view data of test case"""

    def get_case_logs(self, testcase):
        content_type = self.get_case_content_type()
        logs = TCMSLogModel.objects.filter(content_type=content_type,
                                           object_pk=testcase.pk,
                                           site=settings.SITE_ID)
        logs = logs.values('date', 'who__username', 'action')
        return logs.order_by('date')

    def get_case_comments(self, case):
        """Get a case' comments"""

        content_type = self.get_case_content_type()
        comments = Comment.objects.filter(content_type=content_type,
                                          object_pk=case.pk,
                                          site=settings.SITE_ID,
                                          is_removed=False)
        comments = comments.select_related('user').only('submit_date',
                                                        'user__email',
                                                        'comment')
        comments.order_by('pk')
        return comments

    @staticmethod
    def get_case_content_type():
        return ContentType.objects.get_for_model(TestCase)


class TestCaseRunViewDataMixin(object):
    """Mixin class to get view data of test case run"""

    def get_case_run_logs(self, caserun):
        content_type = self.get_case_run_content_type()
        logs = TCMSLogModel.objects.filter(content_type=content_type,
                                           object_pk=caserun.pk,
                                           site_id=settings.SITE_ID)
        return logs.values('date', 'who__username', 'action')

    def get_case_run_comments(self, caserun):
        content_type = self.get_case_run_content_type()
        comments = Comment.objects.filter(content_type=content_type,
                                          object_pk=caserun.pk,
                                          site_id=settings.SITE_ID,
                                          is_removed=False)
        return comments.values('user__username', 'submit_date', 'comment',
                               'pk', 'user__pk')

    @staticmethod
    def get_case_run_content_type():
        return ContentType.objects.get_for_model(TestCaseRun)
