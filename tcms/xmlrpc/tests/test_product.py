# -*- coding: utf-8 -*-
from xmlrpclib import Fault

from django.contrib.auth.models import User
from django.test import TestCase

from tcms.xmlrpc.api import product
from tcms.xmlrpc.tests.utils import make_http_request


class AssertMessage(object):
    NOT_VALIDATE_ARGS = "Missing validations for args."
    NOT_VALIDATE_REQUIRED_ARGS = "Missing validations for required args."
    NOT_VALIDATE_ILLEGAL_ARGS = "Missing validations for illegal args."
    NOT_VALIDATE_FOREIGN_KEY = "Missing validations for foreign key."
    NOT_VALIDATE_LENGTH = "Missing validations for length of value."
    NOT_VALIDATE_URL_FORMAT = "Missing validations for URL format."

    SHOULD_BE_400 = "Error code should be 400."
    SHOULD_BE_409 = "Error code should be 409."
    SHOULD_BE_500 = "Error code should be 500."
    SHOULD_BE_403 = "Error code should be 403."
    SHOULD_BE_401 = "Error code should be 401."
    SHOULD_BE_404 = "Error code should be 404."
    SHOULD_BE_501 = "Error code should be 501."
    SHOULD_BE_1 = "Error code should be 1."

    UNEXCEPT_ERROR = "Unexcept error occurs."
    NEED_ENCODE_UTF8 = "Need to encode with utf8."

    NOT_IMPLEMENT_FUNC = "Not implement yet."
    XMLRPC_INTERNAL_ERROR = "xmlrpc library error."
    NOT_VALIDATE_PERMS = "Missing validations for user perms."


class TestCheckCategory(TestCase):
    def test_check_category(self):
        try:
            cat = product.check_category(None, "--default--", 1)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(cat['name'], "--default--")

    def test_check_category_with_non_exist(self):
        try:
            product.check_category(None, "NonExist", 1)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

        try:
            product.check_category(None, "--default--", 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

    def test_check_category_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.check_category(None, "--default--", arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        for arg in bad_args:
            try:
                product.check_category(None, arg, "--default--")
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestCheckComponent(TestCase):
    def test_check_component(self):
        try:
            cat = product.check_component(None, "P", 1)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(cat['name'], "P")

    def test_check_component_with_non_exist(self):
        try:
            product.check_component(None, "NonExist", 1)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

        try:
            product.check_component(None, "P", 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

    def test_check_component_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.check_component(None, "P", arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        for arg in bad_args:
            try:
                product.check_component(None, arg, "P")
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestCheckProduct(TestCase):
    def test_check_product(self):
        try:
            cat = product.check_product(None, "StarCraft")
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(cat['name'], "StarCraft")

    def test_check_product_with_non_exist(self):
        try:
            product.check_product(None, "NonExist")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

    def test_check_product_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.check_product(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestFilter(TestCase):
    def test_filter_by_id(self):
        try:
            prod = product.filter(None, {
                "id": 1
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(prod)
            self.assertEqual(prod[0]['name'], "StarCraft")

    def test_filter_by_name(self):
        try:
            prod = product.filter(None, {
                "name": "StarCraft"
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(prod)
            self.assertEqual(prod[0]['name'], "StarCraft")

    def test_filter_by_non_doc_fields(self):
        try:
            product.filter(None, {
                "disallow_new": False
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestFilterCategories(TestCase):
    def test_filter_by_id(self):
        try:
            cat = product.filter_categories(None, {
                "id": 1
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(cat)
            self.assertEqual(cat[0]['name'], "--default--")

    def test_filter_by_name(self):
        try:
            cat = product.filter_categories(None, {
                "name": "--default--"
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(cat)
            self.assertEqual(cat[0]['name'], "--default--")


class TestFilterComponents(TestCase):
    def test_filter_by_id(self):
        try:
            com = product.filter_components(None, {
                "id": 1
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(com)
            self.assertEqual(com[0]['name'], "T")

    def test_filter_by_name(self):
        try:
            com = product.filter_components(None, {
                "name": "T"
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(com)
            self.assertEqual(com[0]['name'], "T")


class TestFilterVersions(TestCase):
    def test_filter_by_id(self):
        try:
            ver = product.filter_versions(None, {
                "id": 1
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(ver)
            self.assertEqual(ver[0]['value'], "unspecified")

    def test_filter_by_name(self):
        try:
            ver = product.filter_versions(None, {
                "value": "0.7"
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(ver)
            self.assertEqual(ver[0]['value'], "0.7")


class TestGet(TestCase):
    def test_get_product(self):
        try:
            cat = product.get(None, 1)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(cat['name'], "StarCraft")

    def test_get_product_with_non_exist(self):
        try:
            product.get(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

    def test_get_product_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestGetBuilds(TestCase):
    def test_get_build_with_id(self):
        try:
            builds = product.get_builds(None, 1)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(builds)
            self.assertEqual(len(builds), 4)

    def test_get_build_with_name(self):
        try:
            builds = product.get_builds(None, "StarCraft")
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(builds)
            self.assertEqual(len(builds), 4)

    def test_get_build_with_non_exist_prod(self):
        try:
            product.get_builds(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            product.get_builds(None, "Unknown Product")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_build_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_builds(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestGetCases(TestCase):
    def test_get_case_with_id(self):
        try:
            cases = product.get_cases(None, 1)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(cases)
            self.assertEqual(len(cases), 16)

    def test_get_case_with_name(self):
        try:
            cases = product.get_cases(None, "StarCraft")
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(cases)
            self.assertEqual(len(cases), 16)

    def test_get_case_with_non_exist_prod(self):
        try:
            product.get_cases(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            product.get_cases(None, "Unknown Product")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_case_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_cases(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestGetCategories(TestCase):
    def test_get_categories_with_id(self):
        try:
            cats = product.get_categories(None, 1)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(cats)
            self.assertEqual(len(cats), 1)
            self.assertTrue(cats[0]['name'], '--default--')

    def test_get_categories_with_name(self):
        try:
            cats = product.get_categories(None, "StarCraft")
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(cats)
            self.assertEqual(len(cats), 1)
            self.assertEqual(cats[0]['name'], '--default--')

    def test_get_categories_with_non_exist_prod(self):
        try:
            product.get_categories(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            product.get_categories(None, "Unknown Product")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_categories_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_categories(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestGetCategory(TestCase):
    def test_get_category(self):
        try:
            cat = product.get_category(None, 1)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(cat['name'], "--default--")

    def test_get_category_with_non_exist(self):
        try:
            product.get_category(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

    def test_get_category_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_category(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestAddComponent(TestCase):
    def setUp(self):
        super(TestAddComponent, self).setUp()

        self.admin = User(username='tcr_admin',
                          email='tcr_admin@example.com')
        self.staff = User(username='tcr_staff',
                          email='tcr_staff@example.com')
        self.admin.save()
        self.staff.save()
        self.admin_request = make_http_request(
            user=self.admin,
            user_perm='management.add_component'
        )
        self.staff_request = make_http_request(
            user=self.staff
        )

    def tearDown(self):
        super(TestAddComponent, self).tearDown()

        self.admin.delete()
        self.staff.delete()

    def test_add_component(self):
        try:
            com = product.add_component(self.admin_request, 1, "MyComponent")
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(com)
            self.assertEqual(com['name'], 'MyComponent')
            self.assertEqual(com['initial_owner'], 'tcr_admin')

    def test_add_component_with_no_perms(self):
        try:
            product.add_component(self.staff_request, 1, "MyComponent")
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_PERMS)

    def test_add_component_with_non_exist(self):
        try:
            product.add_component(self.admin_request, 99999, "MyComponent")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_PERMS)


class TestGetComponent(TestCase):
    def test_get_component(self):
        try:
            com = product.get_component(None, 1)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(com['name'], "T")

    def test_get_component_with_non_exist(self):
        try:
            product.get_component(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

    def test_get_component_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_component(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestUpdateComponent(TestCase):
    def setUp(self):
        super(TestUpdateComponent, self).setUp()

        self.admin = User(username='tcr_admin',
                          email='tcr_admin@example.com')
        self.staff = User(username='tcr_staff',
                          email='tcr_staff@example.com')
        self.admin.save()
        self.staff.save()
        self.admin_request = make_http_request(
            user=self.admin,
            user_perm='management.change_component'
        )
        self.staff_request = make_http_request(
            user=self.staff
        )

        from tcms.management.models import Component

        self.new_component = Component(name="New Component",
                                       product_id=1,
                                       description="Test")
        self.new_component.save()

    def tearDown(self):
        super(TestUpdateComponent, self).tearDown()

        self.admin.delete()
        self.staff.delete()
        self.new_component.delete()

    def test_update_component(self):
        try:
            pk = self.new_component.pk
            com = product.update_component(self.admin_request, pk, {
                "name": "Updated."
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(com['name'], 'Updated.')

    def test_update_component_with_non_exist(self):
        try:
            product.update_component(self.admin_request, 1111, {})
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_component_with_no_perms(self):
        try:
            product.update_component(self.staff_request, 1, {})
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_PERMS)

    def test_update_component_with_no_arg(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.update_component(self.admin_request,
                                         self.new_component.pk, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        for arg in bad_args:
            try:
                product.update_component(self.admin_request, arg, {})
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestGetComponents(TestCase):
    def test_get_components_with_id(self):
        try:
            coms = product.get_components(None, 1)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(coms)
            self.assertEqual(len(coms), 3)
            names = list((plan['name'] for plan in coms))
            self.assertTrue('P' in names and 'T' in names and 'Z' in names)

    def test_get_components_with_name(self):
        try:
            coms = product.get_components(None, "StarCraft")
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(coms)
            self.assertEqual(len(coms), 3)
            names = list((plan['name'] for plan in coms))
            self.assertTrue('P' in names and 'T' in names and 'Z' in names)

    def test_get_components_with_non_exist_prod(self):
        try:
            product.get_components(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            product.get_components(None, "Unknown Product")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_components_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_components(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestGetEnvironments(TestCase):
    def test_get_environments(self):
        try:
            product.get_environments(None, None)
        except Fault as f:
            self.assertEqual(f.faultCode, 501, AssertMessage.SHOULD_BE_501)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)


class TestGetMilestones(TestCase):
    def test_get_milestones(self):
        try:
            product.get_milestones(None, None)
        except Fault as f:
            self.assertEqual(f.faultCode, 501, AssertMessage.SHOULD_BE_501)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)


class TestGetPlans(TestCase):
    def test_get_plans_with_id(self):
        try:
            plans = product.get_plans(None, 1)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(plans)
            self.assertEqual(len(plans), 1)
            self.assertEqual(plans[0]['name'], 'StarCraft: Init')

    def test_get_plans_with_name(self):
        try:
            plans = product.get_plans(None, "StarCraft")
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(plans)
            self.assertEqual(len(plans), 1)
            self.assertEqual(plans[0]['name'], 'StarCraft: Init')

    def test_get_plans_with_non_exist_prod(self):
        try:
            product.get_plans(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            product.get_plans(None, "Unknown Product")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_plans_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_plans(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestGetRuns(TestCase):
    def test_get_runs_with_id(self):
        try:
            runs = product.get_runs(None, 1)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(runs)
            self.assertEqual(len(runs), 2)
            self.assertEqual(runs[0]['summary'], 'Test run for StarCraft: '
                                                 'Init on Unknown environment')

    def test_get_runs_with_name(self):
        try:
            runs = product.get_runs(None, "StarCraft")
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(runs)
            self.assertEqual(len(runs), 2)
            self.assertEqual(runs[0]['summary'], 'Test run for StarCraft: '
                                                 'Init on Unknown environment')

    def test_get_runs_with_non_exist_prod(self):
        try:
            product.get_runs(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            product.get_runs(None, "Unknown Product")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_runs_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_runs(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestGetTag(TestCase):
    def test_get_tag(self):
        try:
            tag = product.get_tag(None, 1)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(tag['name'], "QWER")

    def test_get_tag_with_non_exist(self):
        try:
            product.get_tag(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.UNEXCEPT_ERROR)

    def test_get_tag_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_tag(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestAddVersion(TestCase):
    def setUp(self):
        super(TestAddVersion, self).setUp()

        self.admin = User(username='tcr_admin',
                          email='tcr_admin@example.com')
        self.staff = User(username='tcr_staff',
                          email='tcr_staff@example.com')
        self.admin.save()
        self.staff.save()
        self.admin_request = make_http_request(
            user=self.admin,
            user_perm='management.add_version'
        )
        self.staff_request = make_http_request(
            user=self.staff
        )

    def tearDown(self):
        super(TestAddVersion, self).tearDown()

        self.admin.delete()
        self.staff.delete()

    def test_add_version_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.add_version(self.admin_request, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_add_version_with_id(self):
        try:
            prod = product.add_version(self.admin_request, {
                "product": 1,
                "value": "New Version 1"
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(prod['value'], "New Version 1")
            self.assertEqual(prod['product_id'], 1)

    def test_add_version_with_name(self):
        try:
            prod = product.add_version(self.admin_request, {
                "product": "StarCraft",
                "value": "New Version 2"
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertEqual(prod['value'], "New Version 2")
            self.assertEqual(prod['product_id'], 1)

    def test_add_version_with_non_exist_prod(self):
        try:
            product.get_versions(self.admin_request, {
                "product": 111111,
                "value": "New Version 2"
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_add_version_with_no_required_arg(self):
        try:
            product.get_versions(self.admin_request, {
                "product": 1,
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            product.get_versions(self.admin_request, {
                "value": "New Version 2"
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_add_version_with_illegal_field(self):
        try:
            product.get_versions(self.admin_request, {
                "product": 1,
                "value": "New Version 2",
                "data": "data"
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_add_version_with_no_perms(self):
        try:
            product.add_version(self.staff_request, {})
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_PERMS)


class TestGetVersions(TestCase):
    def test_get_versions_with_id(self):
        try:
            prod = product.get_versions(None, 1)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(prod)
            self.assertEqual(len(prod), 6)
            self.assertEqual(prod[0]['value'], '0.6')
            self.assertEqual(prod[1]['value'], '0.7')
            self.assertEqual(prod[2]['value'], '0.8')
            self.assertEqual(prod[3]['value'], '0.9')
            self.assertEqual(prod[4]['value'], '1.0')
            self.assertEqual(prod[5]['value'], 'unspecified')

    def test_get_versions_with_name(self):
        try:
            prod = product.get_versions(None, "StarCraft")
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(prod)
            self.assertEqual(len(prod), 6)
            self.assertEqual(prod[0]['value'], '0.6')
            self.assertEqual(prod[1]['value'], '0.7')
            self.assertEqual(prod[2]['value'], '0.8')
            self.assertEqual(prod[3]['value'], '0.9')
            self.assertEqual(prod[4]['value'], '1.0')
            self.assertEqual(prod[5]['value'], 'unspecified')

    def test_get_version_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                product.get_versions(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_version_with_non_exist_prod(self):
        try:
            product.get_versions(None, 99999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            product.get_versions(None, "Missing Product")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_version_with_bad_args(self):
        bad_args = (True, False, '', 'aaaa', object)
        for arg in bad_args:
            try:
                product.get_versions(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)
