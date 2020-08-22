# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors

from http import HTTPStatus

from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms.tests import BasePlanCase, LoggedInTestCase, remove_perm_from_user, user_should_have_perm
from tcms.tests.factories import (TagFactory, UserFactory, TestPlanFactory,
                                  ProductFactory, VersionFactory, PlanTypeFactory)
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


class EditPlanViewTest(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        user_should_have_perm(cls.tester, perm='testplans.change_testplan')
        user_should_have_perm(cls.tester, perm='testplans.view_testplan')
        cls.product = ProductFactory()
        cls.product_version = VersionFactory(product=cls.product)
        cls.test_plan_type = PlanTypeFactory()
        cls.test_plan_1 = TestPlanFactory()
        cls.testplan_edit_url = reverse('plan-edit', args=[cls.test_plan_1.pk])

        cls.testplan_edit_data = {
            'author': cls.tester.pk,
            'product': cls.product.pk,
            'product_version': cls.product_version.pk,
            'type': cls.test_plan_type.pk,
            'name': cls.test_plan_1.name,

            'email_settings-0-auto_to_plan_author': 'on',
            'email_settings-0-auto_to_case_owner': 'on',
            'email_settings-0-auto_to_case_default_tester': 'on',
            'email_settings-0-notify_on_case_update': 'on',
            'email_settings-0-notify_on_plan_update': 'on',

            'email_settings-0-id': cls.test_plan_1.emailing.pk,
            'email_settings-TOTAL_FORMS': '1',
            'email_settings-INITIAL_FORMS': '1',
            'email_settings-MIN_NUM_FORMS': '0',
            'email_settings-MAX_NUM_FORMS': '1',
            'is_active': True,
        }

    def test_show_testplan_edit_page(self):
        response = self.client.get(self.testplan_edit_url)
        self.assertContains(response, _('Edit TestPlan'))
        self.assert_notify_form(response)
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="is_active" type="checkbox" checked>',
            html=True)

    def test_edit_testplan_text_field(self):
        edit_data = self.testplan_edit_data.copy()
        new_text = 'Edited: {0}'.format(self.test_plan_1.text)
        edit_data['text'] = new_text

        response = self.client.post(self.testplan_edit_url, data=edit_data, follow=True)

        self.assertContains(response, new_text, html=True)
        self.test_plan_1.refresh_from_db()
        self.assertEqual(new_text, self.test_plan_1.text)

    def test_with_invalid_notify_form_value(self):
        # Note: Boolean fields are always valid - either False or True
        # https://github.com/kiwitcms/Kiwi/pull/1677#discussion_r438776178
        # That's why the only way to make the notify formset invalid is to
        # reference a non-existing email_settings ID !!!
        edit_data = self.testplan_edit_data.copy()
        edit_data['email_settings-0-id'] = -1
        del edit_data['email_settings-0-auto_to_plan_author']

        response = self.client.post(self.testplan_edit_url, data=edit_data, follow=True)

        self.assertContains(response, _('Edit TestPlan'))
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-auto_to_plan_author" '
            'type="checkbox">', html=True)

    def test_with_invalid_product_shows_error(self):
        edit_data = self.testplan_edit_data.copy()
        edit_data['product'] = -1
        del edit_data['email_settings-0-auto_to_plan_author']

        response = self.client.post(self.testplan_edit_url, data=edit_data, follow=True)

        self.assertContains(response, _('Edit TestPlan'))
        self.assertContains(
            response,
            _('Select a valid choice. That choice is not one of the available choices.'))
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-auto_to_plan_author" '
            'type="checkbox">', html=True)

    def test_with_invalid_type_shows_error(self):
        edit_data = self.testplan_edit_data.copy()
        edit_data['type'] = -1
        del edit_data['email_settings-0-auto_to_case_owner']

        response = self.client.post(self.testplan_edit_url, data=edit_data, follow=True)

        self.assertContains(response, _('Edit TestPlan'))
        self.assertContains(
            response,
            _('Select a valid choice. That choice is not one of the available choices.'))
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-auto_to_case_owner" '
            'type="checkbox">', html=True)

    def test_with_invalid_version_shows_error(self):
        edit_data = self.testplan_edit_data.copy()
        # Note: version not assigned to the current Product, that's why
        # it is invalid !
        version = VersionFactory()
        edit_data['product_version'] = version.pk

        response = self.client.post(self.testplan_edit_url, data=edit_data, follow=True)

        self.assertContains(
            response,
            _('Select a valid choice. That choice is not one of the available choices.'))

    def assert_notify_form(self, response):
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-auto_to_plan_author" '
            'type="checkbox" checked>', html=True)
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-auto_to_case_owner" '
            'type="checkbox" checked>', html=True)
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-auto_to_case_default_tester" '
            'type="checkbox" checked>', html=True)
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-notify_on_case_update" '
            'type="checkbox" checked>', html=True)
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-notify_on_plan_update" '
            'type="checkbox" checked>', html=True)
