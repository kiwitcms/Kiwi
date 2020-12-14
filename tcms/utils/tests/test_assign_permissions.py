from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.test import TestCase

from tcms.utils.permissions import assign_default_group_permissions


class TestAssignDefaultGroupPermissions(TestCase):
    """Test utils.permissions.assign_default_group_permissions()"""

    def setUp(self):
        self.admin = Group.objects.get(name="Administrator")
        self.admin.permissions.all().delete()
        self.tester = Group.objects.get(name="Tester")
        self.tester.permissions.all().delete()

    def test_administrator_has_all_permissions(self):
        assign_default_group_permissions()
        self.assertEqual(
            Permission.objects.all().count(), self.admin.permissions.count()
        )

    def test_tester_has_kiwi_apps_permissions(self):
        kiwi_apps = [
            "django_comments",
            "linkreference",
            "management",
            "testcases",
            "testplans",
            "testruns",
        ]
        if "tcms.bugs.apps.AppConfig" in settings.INSTALLED_APPS:
            kiwi_apps.append("bugs")

        assign_default_group_permissions()
        for app_name in kiwi_apps:
            self.assertTrue(
                self.tester.permissions.filter(
                    pk__in=Permission.objects.filter(
                        content_type__app_label__contains=app_name
                    )
                ).exists()
            )
            self.assertEqual(
                Permission.objects.filter(
                    content_type__app_label__contains=app_name
                ).count(),
                self.tester.permissions.filter(
                    content_type__app_label__contains=app_name
                ).count(),
            )

        self.assertTrue(
            self.tester.permissions.filter(
                pk__in=Permission.objects.filter(
                    content_type__app_label__contains="attachments"
                )
            ).exists()
        )
        self.assertEqual(
            Permission.objects.filter(
                content_type__app_label__contains="attachments"
            ).count(),
            self.tester.permissions.filter(
                content_type__app_label__contains="attachments"
            ).count()
            + 1,
        )

        self.assertFalse(
            self.tester.permissions.filter(
                content_type__app_label="attachments",
                codename="delete_foreign_attachments",
            ).exists()
        )

        kiwi_apps.append("attachments")
        self.assertFalse(
            self.tester.permissions.exclude(
                content_type__app_label__in=kiwi_apps
            ).exists()
        )
