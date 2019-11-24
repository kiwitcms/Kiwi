# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors

from http import HTTPStatus

from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from tcms.tests import BasePlanCase, remove_perm_from_user
from tcms.tests.factories import TagFactory, UserFactory
from tcms.utils.permissions import initiate_user_with_default_setups


class TestViewPlanTags(BasePlanCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        initiate_user_with_default_setups(cls.tester)
        for _i in range(3):
            cls.plan.add_tag(TagFactory())

        cls.unauthorized = UserFactory()
        cls.unauthorized.set_password('password')
        cls.unauthorized.save()

        cls.unauthorized.user_permissions.add(*Permission.objects.all())
        remove_perm_from_user(cls.unauthorized, 'testplans.add_testplantag')
        remove_perm_from_user(cls.unauthorized, 'testplans.delete_testplantag')

    def test_view_tags_with_permissions(self):
        url = reverse('ajax-tags')
        response = self.client.get(url, {'plan': self.plan.pk}, follow=True)
        self.assertEqual(HTTPStatus.OK, response.status_code)

        # assert tag actions are shown
        self.assertContains(response, _('Add Tag'))
        self.assertContains(response,
                            'class="remove js-remove-tag" title="remove tag">%s</a>' %
                            _('Remove'))

    def test_view_tags_without_permissions(self):
        self.client.logout()

        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.unauthorized.username,
            password='password')

        url = reverse('ajax-tags')
        response = self.client.get(url, {'plan': self.plan.pk}, follow=True)
        self.assertEqual(HTTPStatus.OK, response.status_code)

        # assert tag actions are shown
        self.assertNotContains(response, 'Add Tag')
        self.assertContains(response, '<span class="disabled grey">%s</span>' % _('Remove'))
