# -*- coding: utf-8 -*-

from http import HTTPStatus

from django.urls import reverse
from django.contrib.auth.models import Permission

from tcms.tests.factories import TagFactory
from tcms.tests.factories import UserFactory
from tcms.tests import remove_perm_from_user
from tcms.tests import BasePlanCase
from tcms.utils.permissions import initiate_user_with_default_setups


class TestViewCaseTags(BasePlanCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        initiate_user_with_default_setups(cls.tester)
        for _ in range(3):
            cls.case.add_tag(TagFactory())

        cls.unauthorized = UserFactory()
        cls.unauthorized.set_password('password')
        cls.unauthorized.save()

        cls.unauthorized.user_permissions.add(*Permission.objects.all())
        remove_perm_from_user(cls.unauthorized, 'testcases.add_testcasetag')
        remove_perm_from_user(cls.unauthorized, 'testcases.delete_testcasetag')

    def test_view_tags_with_permissions(self):
        url = reverse('ajax-tags')
        response = self.client.get(url, {'case': self.case.pk})
        self.assertEqual(HTTPStatus.OK, response.status_code)

        # assert tag actions are shown
        self.assertContains(response, 'Add Tag')
        self.assertContains(response, 'class="remove js-remove-tag" title="remove tag">Remove</a>')

    def test_view_tags_without_permissions(self):
        self.client.logout()

        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.unauthorized.username,
            password='password')

        url = reverse('ajax-tags')
        response = self.client.get(url, {'case': self.case.pk})
        self.assertEqual(HTTPStatus.OK, response.status_code)

        # assert tag actions are shown
        self.assertNotContains(response, 'Add Tag')
        self.assertContains(response, '<span class="disabled grey">Remove</span>')
