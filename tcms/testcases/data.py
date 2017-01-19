# -*- coding: utf-8 -*-

from django.conf import settings
from django_comments.models import Comment
from django.contrib.contenttypes.models import ContentType

from tcms.core.logs.models import TCMSLogModel
from tcms.testcases.models import TestCase
from tcms.testruns.models import TestCaseRun


class TestCaseViewDataMixin(object):
    '''Mixin class to get view data of test case'''

    def get_case_contenttype(self):
        return ContentType.objects.get_for_model(TestCase)

    def get_case_logs(self, testcase):
        ct = self.get_case_contenttype()
        logs = TCMSLogModel.objects.filter(content_type=ct,
                                           object_pk=testcase.pk,
                                           site=settings.SITE_ID)
        logs = logs.values('date', 'who__username', 'action')
        return logs.order_by('date')

    def get_case_comments(self, case):
        '''Get a case' comments'''
        ct = self.get_case_contenttype()
        comments = Comment.objects.filter(content_type=ct,
                                          object_pk=case.pk,
                                          site=settings.SITE_ID,
                                          is_removed=False)
        comments = comments.select_related('user').only('submit_date',
                                                        'user__email',
                                                        'user__username',
                                                        'comment')
        comments.order_by('pk')
        return comments


class TestCaseRunViewDataMixin(object):
    '''Mixin class to get view data of test case run'''

    def get_caserun_contenttype(self):
        return ContentType.objects.get_for_model(TestCaseRun)

    def get_caserun_logs(self, caserun):
        caserun_ct = self.get_caserun_contenttype()
        logs = TCMSLogModel.objects.filter(content_type=caserun_ct,
                                           object_pk=caserun.pk,
                                           site_id=settings.SITE_ID)
        return logs.values('date', 'who__username', 'action')

    def get_caserun_comments(self, caserun):
        caserun_ct = self.get_caserun_contenttype()
        comments = Comment.objects.filter(content_type=caserun_ct,
                                          object_pk=caserun.pk,
                                          site_id=settings.SITE_ID,
                                          is_removed=False)
        return comments.values('user__email', 'submit_date', 'comment',
                               'pk', 'user__pk')
