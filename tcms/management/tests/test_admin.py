from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms.management.models import Component
from tcms.tests import LoggedInTestCase
from tcms.tests.factories import BuildFactory
from tcms.utils.permissions import initiate_user_with_default_setups


class TestComponentAdmin(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)

    def test_generated_database_queries(self):
        expected_query = str(
            Component.objects.select_related("product", "initial_owner")
            .order_by("name", "-id")
            .query
        )
        with CaptureQueriesContext(connection) as context:
            self.client.get(reverse("admin:management_component_changelist"))
            for query in context.captured_queries:
                if expected_query == query["sql"]:
                    break
            else:
                self.fail("Component select related query not found.")


class TestBuildAdmin(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)
        cls.build = BuildFactory()

    def test_changelist_view_product_name(self):
        response = self.client.get(reverse("admin:management_build_changelist"))
        self.assertContains(response, _("Product"))
        self.assertContains(response, self.build.version.product)
