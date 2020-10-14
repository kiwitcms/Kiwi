# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

from xmlrpc.client import Fault, ProtocolError

from django.contrib.auth.models import Permission
from tcms_api import xmlrpc

from tcms.core.helpers import comments
from tcms.management.models import Priority
from tcms.rpc.tests.utils import APITestCase, APIPermissionsTestCase
from tcms.testcases.models import Category, TestCase, TestCaseStatus
from tcms.tests import remove_perm_from_user
from tcms.tests.factories import (CategoryFactory, ComponentFactory,
                                  ProductFactory, TagFactory, TestCaseFactory,
                                  TestPlanFactory, UserFactory, VersionFactory)


class TestNotificationRemoveCC(APITestCase):
    """ Tests the XML-RPC testcase.notication_remove_cc method """

    def _fixture_setup(self):
        super()._fixture_setup()

        self.default_cc = 'example@MrSenko.com'
        self.testcase = TestCaseFactory()
        self.testcase.emailing.add_cc(self.default_cc)

    def tearDown(self):
        super().tearDown()
        self.rpc_client.Auth.logout()

    def test_remove_existing_cc(self):
        # initially testcase has the default CC listed
        # and we issue XMLRPC request to remove the cc
        self.rpc_client.TestCase.remove_notification_cc(self.testcase.pk, [self.default_cc])

        # now verify that the CC email has been removed
        self.testcase.emailing.refresh_from_db()
        self.assertEqual([], self.testcase.emailing.get_cc_list())


class TestFilterCases(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.tester = UserFactory(username='great tester')
        self.product = ProductFactory(name='StarCraft')
        self.version = VersionFactory(value='0.1', product=self.product)
        self.plan = TestPlanFactory(name='Test product.get_cases',
                                    author=self.tester,
                                    product=self.product,
                                    product_version=self.version)
        self.case_category = CategoryFactory(product=self.product)
        self.cases_count = 10
        self.cases = []
        for _ in range(self.cases_count):
            test_case = TestCaseFactory(
                category=self.case_category,
                author=self.tester,
                reviewer=self.tester,
                default_tester=None,
                plan=[self.plan])
            self.cases.append(test_case)

    def test_filter_by_product_id(self):
        cases = self.rpc_client.TestCase.filter({'category__product': self.product.pk})
        self.assertIsNotNone(cases)
        self.assertEqual(len(cases), self.cases_count)


class TestUpdate(APITestCase):
    non_existing_username = 'FakeUsername'
    non_existing_user_id = 999
    non_existing_email = 'fake@email.com'

    def _fixture_setup(self):
        super()._fixture_setup()

        self.testcase = TestCaseFactory(summary='Sanity test case',
                                        text='Given-When-Then',
                                        default_tester=None)
        self.new_author = UserFactory()

    def test_update_text_and_product(self):
        author_pk = self.testcase.author.pk
        self.assertEqual('Sanity test case', self.testcase.summary)
        self.assertEqual('Given-When-Then', self.testcase.text)

        # update the test case
        updated = self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                'summary': 'This was updated',
                'text': 'new TC text',
            }
        )

        self.testcase.refresh_from_db()

        self.assertEqual(updated['id'], self.testcase.pk)
        self.assertEqual('This was updated', self.testcase.summary)
        self.assertEqual('new TC text', self.testcase.text)
        # FK for author not passed above. Make sure it didn't change!
        self.assertEqual(author_pk, self.testcase.author.pk)

    def test_update_author_issue_630(self):
        self.assertNotEqual(self.new_author, self.testcase.author)

        # update the test case
        updated = self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                'author': self.new_author.pk,
            }
        )

        self.testcase.refresh_from_db()
        self.assertEqual(self.new_author, self.testcase.author)
        self.assertEqual(self.new_author.pk, updated['author_id'])

    def test_update_author_should_fail_for_non_existing_user_id(self):
        initial_author_id = self.testcase.author.pk
        with self.assertRaises(Fault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    'author': self.non_existing_user_id,
                }
            )

        self.testcase.refresh_from_db()
        self.assertEqual(initial_author_id, self.testcase.author.pk)

    def test_update_author_accepts_username(self):
        self.assertNotEqual(self.new_author, self.testcase.author)

        # update the test case
        updated = self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                'author': self.new_author.username,
            }
        )

        self.testcase.refresh_from_db()
        self.assertEqual(self.new_author, self.testcase.author)
        self.assertEqual(self.new_author.pk, updated['author_id'])

    def test_update_author_should_fail_for_non_existing_username(self):
        initial_author_username = self.testcase.author.username
        with self.assertRaises(Fault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    'author': self.non_existing_username,
                }
            )

        self.testcase.refresh_from_db()
        self.assertEqual(initial_author_username, self.testcase.author.username)

    def test_update_author_accepts_email(self):
        self.assertNotEqual(self.new_author, self.testcase.author)

        # update the test case
        updated = self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                'author': self.new_author.email,
            }
        )

        self.testcase.refresh_from_db()
        self.assertEqual(self.new_author, self.testcase.author)
        self.assertEqual(self.new_author.pk, updated['author_id'])

    def test_update_author_should_fail_for_non_existing_email(self):
        initial_author_email = self.testcase.author.email
        with self.assertRaises(Fault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    'author': self.non_existing_email,
                }
            )

        self.testcase.refresh_from_db()
        self.assertEqual(initial_author_email, self.testcase.author.email)

    def test_update_priority_issue_1318(self):
        expected_priority = Priority.objects.exclude(pk=self.testcase.priority.pk).first()

        self.assertNotEqual(expected_priority.pk, self.testcase.priority.pk)
        self.assertEqual('Sanity test case', self.testcase.summary)
        self.assertEqual('Given-When-Then', self.testcase.text)

        # update the test case
        self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                'priority': expected_priority.pk,
            }
        )

        self.testcase.refresh_from_db()

        # priority has changed
        self.assertEqual(expected_priority.pk, self.testcase.priority.pk)

        # but nothing else changed, issue #1318
        self.assertEqual('Sanity test case', self.testcase.summary)
        self.assertEqual('Given-When-Then', self.testcase.text)

    def test_update_default_tester_accepts_user_id(self):
        self.assertIsNone(self.testcase.default_tester)

        self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                'default_tester': self.new_author.pk,
            }
        )

        self.testcase.refresh_from_db()

        self.assertEqual(self.new_author.pk, self.testcase.default_tester.pk)

    def test_update_default_tester_should_fail_with_non_existing_user_id(self):
        self.assertIsNone(self.testcase.default_tester)

        with self.assertRaises(Fault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    'default_tester': self.non_existing_user_id,
                }
            )

        self.testcase.refresh_from_db()

        self.assertIsNone(self.testcase.default_tester)

    def test_update_default_tester_accepts_username(self):
        self.assertIsNone(self.testcase.default_tester)

        self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                'default_tester': self.new_author.username,
            }
        )

        self.testcase.refresh_from_db()

        self.assertEqual(self.new_author.pk, self.testcase.default_tester.pk)

    def test_update_default_tester_should_fail_with_non_existing_username(self):
        self.assertIsNone(self.testcase.default_tester)

        with self.assertRaises(Fault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    'default_tester': self.non_existing_username,
                }
            )

        self.testcase.refresh_from_db()

        self.assertIsNone(self.testcase.default_tester)

    def test_update_default_tester_accepts_email(self):
        self.assertIsNone(self.testcase.default_tester)
        self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                'default_tester': self.new_author.email,
            }
        )

        self.testcase.refresh_from_db()

        self.assertEqual(self.new_author.pk, self.testcase.default_tester.pk)

    def test_update_default_tester_should_fail_with_non_existing_email(self):
        self.assertIsNone(self.testcase.default_tester)

        with self.assertRaises(Fault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    'default_tester': self.non_existing_email,
                }
            )

        self.testcase.refresh_from_db()

        self.assertIsNone(self.testcase.default_tester)

    def test_update_reviewer_accepts_user_id(self):
        self.assertNotEqual(self.new_author, self.testcase.reviewer)

        self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                'reviewer': self.new_author.pk,
            }
        )

        self.testcase.refresh_from_db()

        self.assertEqual(self.new_author.pk, self.testcase.reviewer.pk)

    def test_update_reviewer_should_fail_with_non_existing_user_id(self):
        initial_reviewer_id = self.testcase.reviewer.pk
        with self.assertRaises(Fault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    'reviewer': self.non_existing_user_id,
                }
            )

        self.testcase.refresh_from_db()
        self.assertEqual(initial_reviewer_id, self.testcase.reviewer.pk)

    def test_update_reviewer_accepts_username(self):
        self.assertNotEqual(self.new_author, self.testcase.reviewer)

        self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                'reviewer': self.new_author.username,
            }
        )

        self.testcase.refresh_from_db()
        self.assertEqual(self.new_author, self.testcase.reviewer)

    def test_update_reviewer_should_fail_for_non_existing_username(self):
        initial_reviewer_username = self.testcase.reviewer.username
        with self.assertRaises(Fault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    'reviewer': self.non_existing_username,
                }
            )

        self.testcase.refresh_from_db()
        self.assertEqual(initial_reviewer_username, self.testcase.reviewer.username)

    def test_update_reviewer_accepts_email(self):
        self.assertNotEqual(self.new_author, self.testcase.author)

        self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                'reviewer': self.new_author.email,
            }
        )

        self.testcase.refresh_from_db()
        self.assertEqual(self.new_author, self.testcase.reviewer)

    def test_update_reviewer_should_fail_for_non_existing_email(self):
        initial_reviewer_email = self.testcase.reviewer.email
        with self.assertRaises(Fault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    'reviewer': self.non_existing_email,
                }
            )

        self.testcase.refresh_from_db()
        self.assertEqual(initial_reviewer_email, self.testcase.reviewer.email)


class TestCreate(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        for _ in range(5):
            CategoryFactory()

    def test_passes_with_valid_data(self):
        result = self.rpc_client.TestCase.create(
            {
                'summary': 'Newly created TC via API',
                'text': 'Given-When-Then',
                'case_status': TestCaseStatus.objects.first().pk,
                'priority': Priority.objects.first().pk,
                'category': Category.objects.first().pk,
            }
        )

        tc_from_db = TestCase.objects.get(summary=result['summary'], text=result['text'])

        self.assertEqual(result['id'], tc_from_db.pk)
        # author field is auto-configured if not passed
        self.assertEqual(result['author'], tc_from_db.author.username)
        self.assertEqual(self.api_user, tc_from_db.author)

    def test_author_can_be_specified(self):
        new_author = UserFactory()
        result = self.rpc_client.TestCase.create(
            {
                'summary': 'TC via API with author',
                'case_status': TestCaseStatus.objects.last().pk,
                'priority': Priority.objects.last().pk,
                'category': Category.objects.last().pk,
                'author': new_author.pk,
            }
        )

        tc_from_db = TestCase.objects.get(summary=result['summary'], author=new_author)

        self.assertEqual(result['id'], tc_from_db.pk)
        self.assertEqual(new_author, tc_from_db.author)

    def test_fails_when_mandatory_fields_not_specified(self):
        with self.assertRaises(Fault):
            self.rpc_client.TestCase.create(
                {
                    'summary': 'TC via API without mandatory FK fields',
                }
            )


class TestAddTag(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.testcase = TestCaseFactory()

        self.tag1 = TagFactory()
        self.tag2 = TagFactory()

    def test_add_tag(self):
        self.rpc_client.TestCase.add_tag(self.testcase.pk, self.tag1.name)
        tag_exists = TestCase.objects.filter(pk=self.testcase.pk, tag__pk=self.tag1.pk).exists()
        self.assertTrue(tag_exists)

    def test_add_tag_without_permissions(self):
        unauthorized_user = UserFactory()
        unauthorized_user.set_password('api-testing')
        unauthorized_user.save()

        unauthorized_user.user_permissions.add(*Permission.objects.all())
        remove_perm_from_user(unauthorized_user, 'testcases.add_testcasetag')

        rpc_client = xmlrpc.TCMSXmlrpc(unauthorized_user.username,
                                       'api-testing',
                                       '%s/xml-rpc/' % self.live_server_url).server

        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            rpc_client.TestCase.add_tag(self.testcase.pk, self.tag1.name)

        # tags were not modified
        tag_exists = TestCase.objects.filter(pk=self.testcase.pk, tag__pk=self.tag1.pk).exists()
        self.assertFalse(tag_exists)


class TestRemoveTag(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.tag0 = TagFactory()
        self.tag1 = TagFactory()

        self.testcase = TestCaseFactory()
        self.testcase.add_tag(self.tag0)

    def test_remove_tag(self):
        self.rpc_client.TestCase.remove_tag(self.testcase.pk, self.tag0.name)
        tag_exists = TestCase.objects.filter(pk=self.testcase.pk, tag__pk=self.tag0.pk).exists()
        self.assertFalse(tag_exists)

    def test_remove_tag_without_permissions(self):
        unauthorized_user = UserFactory()
        unauthorized_user.set_password('api-testing')
        unauthorized_user.save()

        unauthorized_user.user_permissions.add(*Permission.objects.all())
        remove_perm_from_user(unauthorized_user, 'testcases.delete_testcasetag')

        rpc_client = xmlrpc.TCMSXmlrpc(unauthorized_user.username,
                                       'api-testing',
                                       '%s/xml-rpc/' % self.live_server_url).server

        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            rpc_client.TestCase.remove_tag(self.testcase.pk, self.tag0.name)

        # tags were not modified
        tag_exists = TestCase.objects.filter(pk=self.testcase.pk, tag__pk=self.tag0.pk).exists()
        self.assertTrue(tag_exists)

        tag_exists = TestCase.objects.filter(pk=self.testcase.pk, tag__pk=self.tag1.pk).exists()
        self.assertFalse(tag_exists)


class TestAddComponent(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()
        self.test_case = TestCaseFactory()
        self.good_component = ComponentFactory(product=self.test_case.category.product)
        self.bad_component = ComponentFactory()

    def test_add_component_from_same_product_is_allowed(self):
        result = self.rpc_client.TestCase.add_component(self.test_case.pk,
                                                        self.good_component.name)
        self.assertEqual(result['component'][0], self.good_component.pk)

    def test_add_component_from_another_product_is_not_allowed(self):
        with self.assertRaisesRegex(Fault, 'Component matching query does not exist'):
            self.rpc_client.TestCase.add_component(self.test_case.pk, self.bad_component.name)


class TestCaseAddComment(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.case = TestCaseFactory()

    def test_add_comment_with_pk_as_int(self):
        created_comment = self.rpc_client.TestCase.add_comment(
            self.case.pk,
            "Hello World!")

        result = comments.get_comments(self.case)
        self.assertEqual(1, result.count())

        first_comment = result.first()
        self.assertEqual("Hello World!", first_comment.comment)
        self.assertEqual("Hello World!", created_comment['comment'])


class TestCaseSortkeysPermissions(APIPermissionsTestCase):
    permission_label = 'testcases.view_testcase'

    def _fixture_setup(self):
        super()._fixture_setup()

        self.plan = TestPlanFactory()

        # add TCs with non-standard sortkeys
        self.case_1 = TestCaseFactory()
        self.plan.add_case(self.case_1, sortkey=5)

        self.case_2 = TestCaseFactory()
        self.plan.add_case(self.case_2, sortkey=15)

        self.case_3 = TestCaseFactory()
        self.plan.add_case(self.case_3, sortkey=25)

    def verify_api_with_permission(self):
        result = self.rpc_client.TestCase.sortkeys({
            "plan": self.plan.pk,
        })

        for entry in result:
            self.assertEqual(entry['plan_id'], self.plan.pk)

        self.assertEqual(result[0]['case_id'], self.case_1.pk)
        self.assertEqual(result[0]['sortkey'], 5)

        self.assertEqual(result[1]['case_id'], self.case_2.pk)
        self.assertEqual(result[1]['sortkey'], 15)

        self.assertEqual(result[2]['case_id'], self.case_3.pk)
        self.assertEqual(result[2]['sortkey'], 25)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.TestCase.sortkeys({
                "plan": self.plan.pk,
            })


class TestCaseCommentsPermissions(APIPermissionsTestCase):
    permission_label = 'django_comments.view_comment'

    def _fixture_setup(self):
        super()._fixture_setup()

        self.case = TestCaseFactory()
        comments.add_comment([self.case], 'First one', self.tester)
        comments.add_comment([self.case], 'Second one', self.tester)

    def verify_api_with_permission(self):
        result = self.rpc_client.TestCase.comments(self.case.pk)

        self.assertEqual(2, len(result))

        # also takes case to verify functionality b/c the target
        # method under test is very simple
        self.assertEqual(result[0]['comment'], 'First one')
        self.assertEqual(result[1]['comment'], 'Second one')
        for entry in result:
            self.assertEqual(entry['object_pk'], str(self.case.pk))
            self.assertEqual(entry['user'], self.tester.pk)
            self.assertEqual(entry['user_name'], self.tester.username)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.TestCase.comments(self.case.pk)
