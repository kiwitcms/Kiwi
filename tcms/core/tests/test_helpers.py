# -*- coding: utf-8 -*-

from django.contrib.contenttypes.models import ContentType
from django_comments.models import Comment

from tcms.core.helpers.comments import add_comment
from tcms.tests import BasePlanCase
from tcms.tests.factories import UserFactory


class TestAddComments(BasePlanCase):
    """Test comments.add_comment"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.reviewer = UserFactory()

    def test_add_comment_to_case(self):
        cases = [self.case_1, self.case_2]
        add_comment(cases, 'new comment', self.reviewer)

        for case in cases:
            case_ct = ContentType.objects.get_for_model(case.__class__)
            comments = Comment.objects.filter(content_type=case_ct,
                                              object_pk=case.pk)
            self.assertEqual(1, comments.count())

            comment = comments.first()
            self.assertEqual('new comment', comment.comment)
            self.assertEqual(self.reviewer, comment.user)
            self.assertEqual(self.reviewer.username, comment.user_name)
            self.assertEqual(self.reviewer.email, comment.user_email)
            self.assertTrue(comment.is_public)
            self.assertFalse(comment.is_removed)
