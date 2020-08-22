# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, invalid-name, objects-update-used
from xmlrpc.client import Fault as XmlRPCFault
from xmlrpc.client import ProtocolError

from attachments.models import Attachment
from django.contrib.auth.models import Permission
from django.test import override_settings
from tcms_api import xmlrpc

from tcms.rpc.tests.utils import APITestCase, APIPermissionsTestCase
from tcms.testcases.models import TestCasePlan
from tcms.testplans.models import TestPlan
from tcms.tests import remove_perm_from_user
from tcms.tests.factories import (PlanTypeFactory, ProductFactory, TagFactory,
                                  TestCaseFactory, TestPlanFactory,
                                  UserFactory, VersionFactory)


class TestFilter(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.product = ProductFactory()
        self.version = VersionFactory(product=self.product)
        self.tester = UserFactory()
        self.plan_type = PlanTypeFactory()
        self.plan_1 = TestPlanFactory(product_version=self.version,
                                      product=self.product,
                                      author=self.tester,
                                      type=self.plan_type)
        self.plan_2 = TestPlanFactory(product_version=self.version,
                                      product=self.product,
                                      author=self.tester,
                                      type=self.plan_type)

    def test_filter_plans(self):
        plans = self.rpc_client.TestPlan.filter({'pk__in': [self.plan_1.pk, self.plan_2.pk]})
        plan = plans[0]
        self.assertEqual(self.plan_1.name, plan['name'])
        self.assertEqual(self.plan_1.product_version.pk, plan['product_version_id'])
        self.assertEqual(self.plan_1.author.pk, plan['author_id'])

    def test_filter_out_all_plans(self):
        plans_total = TestPlan.objects.all().count()
        self.assertEqual(plans_total, len(self.rpc_client.TestPlan.filter()))
        self.assertEqual(plans_total, len(self.rpc_client.TestPlan.filter({})))


class TestAddTag(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.product = ProductFactory()
        self.plans = [
            TestPlanFactory(author=self.api_user, product=self.product),
            TestPlanFactory(author=self.api_user, product=self.product),
        ]

        self.tag1 = TagFactory(name='xmlrpc_test_tag_1')
        self.tag2 = TagFactory(name='xmlrpc_test_tag_2')

    def test_add_tag(self):
        self.rpc_client.TestPlan.add_tag(self.plans[0].pk, self.tag1.name)
        tag_exists = TestPlan.objects.filter(pk=self.plans[0].pk, tag__pk=self.tag1.pk).exists()
        self.assertTrue(tag_exists)

    def test_add_tag_without_permissions(self):
        unauthorized_user = UserFactory()
        unauthorized_user.set_password('api-testing')
        unauthorized_user.save()

        unauthorized_user.user_permissions.add(*Permission.objects.all())
        remove_perm_from_user(unauthorized_user, 'testplans.add_testplantag')

        rpc_client = xmlrpc.TCMSXmlrpc(unauthorized_user.username,
                                       'api-testing',
                                       '%s/xml-rpc/' % self.live_server_url).server

        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            rpc_client.TestPlan.add_tag(self.plans[0].pk, self.tag1.name)

        # tags were not modified
        tag_exists = TestPlan.objects.filter(pk=self.plans[0].pk, tag__pk=self.tag1.pk).exists()
        self.assertFalse(tag_exists)


class TestRemoveTag(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.product = ProductFactory()
        self.plans = [
            TestPlanFactory(author=self.api_user, product=self.product),
            TestPlanFactory(author=self.api_user, product=self.product),
        ]

        self.tag0 = TagFactory(name='xmlrpc_test_tag_0')
        self.tag1 = TagFactory(name='xmlrpc_test_tag_1')

        self.plans[0].add_tag(self.tag0)
        self.plans[1].add_tag(self.tag1)

    def test_remove_tag(self):
        self.rpc_client.TestPlan.remove_tag(self.plans[0].pk, self.tag0.name)
        tag_exists = TestPlan.objects.filter(pk=self.plans[0].pk, tag__pk=self.tag0.pk).exists()
        self.assertFalse(tag_exists)

    def test_remove_tag_without_permissions(self):
        unauthorized_user = UserFactory()
        unauthorized_user.set_password('api-testing')
        unauthorized_user.save()

        unauthorized_user.user_permissions.add(*Permission.objects.all())
        remove_perm_from_user(unauthorized_user, 'testplans.delete_testplantag')

        rpc_client = xmlrpc.TCMSXmlrpc(unauthorized_user.username,
                                       'api-testing',
                                       '%s/xml-rpc/' % self.live_server_url).server

        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            rpc_client.TestPlan.remove_tag(self.plans[0].pk, self.tag0.name)

        # tags were not modified
        tag_exists = TestPlan.objects.filter(pk=self.plans[0].pk, tag__pk=self.tag0.pk).exists()
        self.assertTrue(tag_exists)

        tag_exists = TestPlan.objects.filter(pk=self.plans[0].pk, tag__pk=self.tag1.pk).exists()
        self.assertFalse(tag_exists)


@override_settings(LANGUAGE_CODE='en')
class TestUpdate(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.plan = TestPlanFactory()

    def test_not_exist_test_plan_id(self):
        err_msg = 'Internal error: TestPlan matching query does not exist.'
        with self.assertRaisesRegex(XmlRPCFault, err_msg):
            self.rpc_client.TestPlan.update(-1, {'text': 'This has been updated'})

    def test_invalid_field_value(self):
        err_msg = 'Select a valid choice. That choice is not one of the available choices.'
        with self.assertRaisesRegex(XmlRPCFault, err_msg):
            self.rpc_client.TestPlan.update(self.plan.pk, {'type': -1})


class TestUpdatePermission(APIPermissionsTestCase):
    permission_label = 'testplans.change_testplan'

    def _fixture_setup(self):
        super()._fixture_setup()

        self.plan = TestPlanFactory()

    def verify_api_with_permission(self):
        self.rpc_client.TestPlan.update(self.plan.pk, {'text': 'This has been updated'})
        # reload from db
        self.plan.refresh_from_db()
        # assert
        self.assertEqual('This has been updated', self.plan.text)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.TestPlan.update(self.plan.pk, {'text': 'This has been updated'})


class TestRemoveCase(APITestCase):
    """ Test the XML-RPC method TestPlan.remove_case() """

    def _fixture_setup(self):
        super()._fixture_setup()
        self.testcase_1 = TestCaseFactory()
        self.testcase_2 = TestCaseFactory()
        self.plan_1 = TestPlanFactory()
        self.plan_2 = TestPlanFactory()

        self.plan_1.add_case(self.testcase_1)
        self.plan_1.add_case(self.testcase_2)

        self.plan_2.add_case(self.testcase_2)

    def test_remove_case_with_single_plan(self):
        self.rpc_client.TestPlan.remove_case(self.plan_1.pk, self.testcase_1.pk)
        self.assertEqual(0, self.testcase_1.plan.count())  # pylint: disable=no-member

    def test_remove_case_with_two_plans(self):
        self.assertEqual(2, self.testcase_2.plan.count())  # pylint: disable=no-member

        self.rpc_client.TestPlan.remove_case(self.plan_1.pk, self.testcase_2.pk)
        self.assertEqual(1, self.testcase_2.plan.count())  # pylint: disable=no-member


class TestAddCase(APITestCase):
    """ Test the XML-RPC method TestPlan.add_case() """

    def _fixture_setup(self):
        super()._fixture_setup()

        self.testcase_1 = TestCaseFactory()
        self.testcase_2 = TestCaseFactory()
        self.testcase_3 = TestCaseFactory()

        self.plan_1 = TestPlanFactory()
        self.plan_2 = TestPlanFactory()
        self.plan_3 = TestPlanFactory()

        # case 1 is already linked to plan 1
        self.plan_1.add_case(self.testcase_1)

    def test_ignores_existing_mappings(self):
        plans = [self.plan_1.pk, self.plan_2.pk, self.plan_3.pk]
        cases = [self.testcase_1.pk, self.testcase_2.pk, self.testcase_3.pk]

        for plan_id in plans:
            for case_id in cases:
                self.rpc_client.TestPlan.add_case(plan_id, case_id)

        # no duplicates for plan1/case1 were created
        self.assertEqual(
            1,
            TestCasePlan.objects.filter(
                plan=self.plan_1.pk,
                case=self.testcase_1.pk
            ).count()
        )

        # verify all case/plan combinations exist
        for plan_id in plans:
            for case_id in cases:
                self.assertEqual(
                    1,
                    TestCasePlan.objects.filter(
                        plan=plan_id,
                        case=case_id
                    ).count()
                )


@override_settings(LANGUAGE_CODE='en')
class TestCreate(APITestCase):
    def test_create_plan_with_empty_required_field(self):
        product = ProductFactory()
        version = VersionFactory(product=product)
        plan_type = PlanTypeFactory()
        with self.assertRaisesRegex(XmlRPCFault, 'This field is required.'):
            self.rpc_client.TestPlan.create({
                'product': product.pk,
                'product_version': version.pk,
                'name': '',
                'type': plan_type.pk,
                'text': 'Testing TCMS',
                'parent': None,
            })

    def test_create_plan_with_different_user(self):
        product = ProductFactory()
        version = VersionFactory(product=product)
        plan_type = PlanTypeFactory()
        user = UserFactory()

        params = {
            'product': product.pk,
            'product_version': version.pk,
            'name': 'test plan',
            'type': plan_type.pk,
            'text': 'Testing TCMS',
            'parent': None,
            'author': user.pk
        }
        result = self.rpc_client.TestPlan.create(params)
        self.assertEqual(params['product'], result['product_id'])
        self.assertEqual(params['product_version'], result['product_version_id'])
        self.assertEqual(params['name'], result['name'])
        self.assertEqual(params['type'], result['type_id'])
        self.assertEqual(params['text'], result['text'])
        self.assertEqual(params['parent'], result['parent'])
        self.assertEqual(user.username, result['author'])
        self.assertEqual(user.pk, result['author_id'])


class TestCreatePermission(APIPermissionsTestCase):
    permission_label = 'testplans.add_testplan'

    def _fixture_setup(self):
        super()._fixture_setup()

        self.product = ProductFactory()
        self.version = VersionFactory(product=self.product)
        self.plan_type = PlanTypeFactory()
        self.params = {
            'product': self.product.pk,
            'product_version': self.version.pk,
            'name': 'Testplan foobar',
            'type': self.plan_type.pk,
            'text': 'Testing TCMS',
            'parent': None,
        }

    def verify_api_with_permission(self):
        result = self.rpc_client.TestPlan.create(self.params)
        self.assertEqual(self.params['product'], result['product_id'])
        self.assertEqual(self.params['product_version'], result['product_version_id'])
        self.assertEqual(self.params['name'], result['name'])
        self.assertEqual(self.params['type'], result['type_id'])
        self.assertEqual(self.params['text'], result['text'])
        self.assertEqual(self.params['parent'], result['parent'])
        self.assertEqual(self.tester.username, result['author'])

        # verify object from DB
        testplan = TestPlan.objects.get(name=self.params['name'])
        self.assertEqual(testplan.serialize(), result)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.TestPlan.create(self.params)


@override_settings(LANGUAGE_CODE='en')
class TestListAttachments(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.plan = TestPlanFactory()

    def test_list_attachments(self):
        file_name = 'attachment.txt'
        self.rpc_client.TestPlan.add_attachment(self.plan.pk, file_name, 'a2l3aXRjbXM=')
        attachments = self.rpc_client.TestPlan.list_attachments(self.plan.pk)
        self.assertEqual(1, len(attachments))

    def test_list_attachments_with_wrong_plan_id(self):
        with self.assertRaisesRegex(XmlRPCFault, 'TestPlan matching query does not exist'):
            self.rpc_client.TestPlan.list_attachments(-1)


class TestListAttachmentsPermissions(APIPermissionsTestCase):
    permission_label = 'attachments.view_attachment'

    def _fixture_setup(self):
        super()._fixture_setup()

        self.plan = TestPlanFactory()

    def verify_api_with_permission(self):
        attachments = self.rpc_client.TestPlan.list_attachments(self.plan.pk)
        self.assertEqual(0, len(attachments))

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.TestPlan.list_attachments(self.plan.pk)


class TestAddAttachmentPermissions(APIPermissionsTestCase):
    permission_label = 'attachments.add_attachment'

    def _fixture_setup(self):
        super()._fixture_setup()

        self.plan = TestPlanFactory()

    def verify_api_with_permission(self):
        file_name = 'attachment.txt'
        self.rpc_client.TestPlan.add_attachment(self.plan.pk, file_name, 'a2l3aXRjbXM=')
        attachments = Attachment.objects.attachments_for_object(self.plan)
        self.assertEqual(1, len(attachments))

        attachment = attachments[0]
        file_url = attachment.attachment_file.url
        self.assertTrue(file_url.startswith('/uploads/attachments/testplans_testplan/'))
        self.assertTrue(file_url.endswith(file_name))

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.TestPlan.add_attachment(self.plan.pk, 'attachment.txt', 'a2l3aXRjbXM=')
