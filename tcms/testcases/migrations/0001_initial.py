# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import migrations, models

import tcms.core.models.base

test_case_statuss = ["PROPOSED", "CONFIRMED", "DISABLED", "NEED_UPDATE"]


CASE_STATUS_ID_COLUMN = "case_status_id"
CATEGORY_ID_COLUMN = "category_id"
if settings.DATABASES["default"]["ENGINE"].find("sqlite") > -1:
    CASE_STATUS_ID_COLUMN = ""
    CATEGORY_ID_COLUMN = ""


def forwards_add_initial_data(apps, schema_editor):
    bug_system_model = apps.get_model("testcases", "BugSystem")
    bug_system_model.objects.bulk_create(
        [
            bug_system_model(
                name="Bugzilla",
                description="1-7 digit, e.g. 1001234",
                url_reg_exp="https://bugzilla.example.com/show_bug.cgi?id=%s",
                validate_reg_exp=r"^\d{1,7}$",
            ),
            bug_system_model(
                name="JIRA",
                description="e.g. KIWI-222",
                url_reg_exp="https://jira.example.com/browse/%s",
                validate_reg_exp=r"^[A-Z0-9]+-\d+$",
            ),
        ]
    )

    test_case_status_model = apps.get_model("testcases", "TestCaseStatus")
    test_case_status_model.objects.bulk_create(
        [
            test_case_status_model(name=name, description="")
            for name in test_case_statuss
        ]
    )


def reverse_add_initial_data(apps, schema_editor):
    bug_system_model = apps.get_model("testcases", "BugSystem")
    bug_system_model.objects.filter(name__in=["Bugzilla", "JIRA"]).delete()

    test_case_status_model = apps.get_model("testcases", "TestCaseStatus")
    test_case_status_model.objects.filter(name__in=test_case_statuss).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("management", "0003_squashed"),
        ("testplans", "0005_squashed"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TestCaseStatus",
            fields=[
                (
                    "id",
                    models.AutoField(
                        max_length=6,
                        serialize=False,
                        primary_key=True,
                        db_column=CASE_STATUS_ID_COLUMN,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(null=True, blank=True)),
            ],
            options={
                "verbose_name": "Test case status",
                "verbose_name_plural": "Test case statuses",
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False, primary_key=True, db_column=CATEGORY_ID_COLUMN
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                (
                    "product",
                    models.ForeignKey(
                        related_name="category",
                        to="management.Product",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "test case categories",
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name="TestCase",
            fields=[
                ("case_id", models.AutoField(serialize=False, primary_key=True)),
                (
                    "create_date",
                    models.DateTimeField(auto_now_add=True, db_column="creation_date"),
                ),
                (
                    "is_automated",
                    models.IntegerField(default=0, db_column="isautomated"),
                ),
                ("is_automated_proposed", models.BooleanField(default=False)),
                ("script", models.TextField(blank=True, null=True)),
                ("arguments", models.TextField(blank=True, null=True)),
                (
                    "extra_link",
                    models.CharField(
                        default=None, max_length=1024, null=True, blank=True
                    ),
                ),
                ("summary", models.CharField(max_length=255)),
                (
                    "requirement",
                    models.CharField(max_length=255, blank=True, null=True),
                ),
                ("alias", models.CharField(max_length=255, blank=True)),
                ("notes", models.TextField(blank=True, null=True)),
            ],
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.AddField(
            model_name="testcase",
            name="author",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name="cases_as_author",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="testcase",
            name="case_status",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE, to="testcases.TestCaseStatus"
            ),
        ),
        migrations.AddField(
            model_name="testcase",
            name="category",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name="category_case",
                to="testcases.Category",
            ),
        ),
        migrations.CreateModel(
            name="TestCaseComponent",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "case",
                    models.ForeignKey(
                        to="testcases.TestCase", on_delete=models.CASCADE
                    ),
                ),
                (
                    "component",
                    models.ForeignKey(
                        to="management.Component", on_delete=models.CASCADE
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="testcase",
            name="component",
            field=models.ManyToManyField(
                related_name="cases",
                through="testcases.TestCaseComponent",
                to="management.Component",
            ),
        ),
        migrations.AddField(
            model_name="testcase",
            name="default_tester",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.CASCADE,
                related_name="cases_as_default_tester",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="TestCasePlan",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("sortkey", models.IntegerField(null=True, blank=True)),
                (
                    "case",
                    models.ForeignKey(
                        to="testcases.TestCase", on_delete=models.CASCADE
                    ),
                ),
                (
                    "plan",
                    models.ForeignKey(
                        to="testplans.TestPlan", on_delete=models.CASCADE
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="testcase",
            name="plan",
            field=models.ManyToManyField(
                related_name="case",
                through="testcases.TestCasePlan",
                to="testplans.TestPlan",
            ),
        ),
        migrations.AddField(
            model_name="testcase",
            name="priority",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name="priority_case",
                to="management.Priority",
            ),
        ),
        migrations.AddField(
            model_name="testcase",
            name="reviewer",
            field=models.ForeignKey(
                null=True,
                on_delete=models.deletion.CASCADE,
                related_name="cases_as_reviewer",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="TestCaseTag",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "case",
                    models.ForeignKey(
                        to="testcases.TestCase", on_delete=models.CASCADE
                    ),
                ),
                (
                    "tag",
                    models.ForeignKey(to="management.Tag", on_delete=models.CASCADE),
                ),
            ],
        ),
        migrations.AddField(
            model_name="testcase",
            name="tag",
            field=models.ManyToManyField(
                related_name="case",
                through="testcases.TestCaseTag",
                to="management.Tag",
            ),
        ),
        migrations.CreateModel(
            name="HistoricalTestCase",
            fields=[
                ("case_id", models.IntegerField(blank=True, db_index=True)),
                (
                    "create_date",
                    models.DateTimeField(
                        blank=True, db_column="creation_date", editable=False
                    ),
                ),
                (
                    "is_automated",
                    models.IntegerField(db_column="isautomated", default=0),
                ),
                ("is_automated_proposed", models.BooleanField(default=False)),
                ("script", models.TextField(blank=True, null=True)),
                ("arguments", models.TextField(blank=True, null=True)),
                (
                    "extra_link",
                    models.CharField(
                        blank=True, default=None, max_length=1024, null=True
                    ),
                ),
                ("summary", models.CharField(max_length=255)),
                (
                    "requirement",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("alias", models.CharField(blank=True, max_length=255)),
                ("notes", models.TextField(blank=True, null=True)),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_change_reason", models.TextField(null=True)),
                ("history_date", models.DateTimeField()),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=models.deletion.DO_NOTHING,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "case_status",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=models.deletion.DO_NOTHING,
                        related_name="+",
                        to="testcases.TestCaseStatus",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=models.deletion.DO_NOTHING,
                        related_name="+",
                        to="testcases.Category",
                    ),
                ),
                (
                    "default_tester",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=models.deletion.DO_NOTHING,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "priority",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=models.deletion.DO_NOTHING,
                        related_name="+",
                        to="management.Priority",
                    ),
                ),
                (
                    "reviewer",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=models.deletion.DO_NOTHING,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical test case",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": "history_date",
            },
        ),
        migrations.CreateModel(
            name="Bug",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("bug_id", models.CharField(max_length=25)),
                ("summary", models.CharField(max_length=255, null=True, blank=True)),
                ("description", models.TextField(null=True, blank=True)),
                (
                    "case",
                    models.ForeignKey(
                        related_name="case_bug",
                        to="testcases.TestCase",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name="BugSystem",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.TextField(blank=True)),
                (
                    "url_reg_exp",
                    models.CharField(
                        max_length=8192,
                        help_text="A valid Python format string such as "
                        "http://bugs.example.com/%s",
                        verbose_name="URL format string",
                    ),
                ),
                (
                    "validate_reg_exp",
                    models.CharField(
                        max_length=128,
                        help_text="A valid JavaScript regular "
                        "expression such as ^\\d$",
                        verbose_name="RegExp for ID validation",
                    ),
                ),
                (
                    "api_url",
                    models.CharField(
                        blank=True,
                        max_length=1024,
                        null=True,
                        verbose_name="API URL",
                        help_text="This is the URL to which API requests "
                        "will be sent. Leave empty to disable!",
                    ),
                ),
                (
                    "api_password",
                    models.CharField(
                        blank=True,
                        max_length=256,
                        null=True,
                        verbose_name="API password or token",
                    ),
                ),
                (
                    "api_username",
                    models.CharField(
                        blank=True,
                        max_length=256,
                        null=True,
                        verbose_name="API username",
                    ),
                ),
                (
                    "tracker_type",
                    models.CharField(
                        default="IssueTrackerType",
                        max_length=128,
                        help_text="This determines how Kiwi TCMS "
                        "integrates with the IT system",
                        verbose_name="Type",
                    ),
                ),
                (
                    "base_url",
                    models.CharField(
                        max_length=1024,
                        null=True,
                        blank=True,
                        verbose_name="Base URL",
                        help_text="""Base URL, for example\
 <strong>https://bugzilla.example.com</strong>!
Leave empty to disable!
""",
                    ),
                ),
            ],
            options={
                "verbose_name": "Bug tracker",
                "verbose_name_plural": "Bug trackers",
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.AddField(
            model_name="bug",
            name="bug_system",
            field=models.ForeignKey(
                default=1, to="testcases.BugSystem", on_delete=models.CASCADE
            ),
        ),
        migrations.CreateModel(
            name="TestCaseEmailSettings",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("notify_on_case_update", models.BooleanField(default=False)),
                ("notify_on_case_delete", models.BooleanField(default=False)),
                ("auto_to_case_author", models.BooleanField(default=False)),
                ("auto_to_case_tester", models.BooleanField(default=False)),
                ("auto_to_run_manager", models.BooleanField(default=False)),
                ("auto_to_run_tester", models.BooleanField(default=False)),
                ("auto_to_case_run_assignee", models.BooleanField(default=False)),
                (
                    "case",
                    models.OneToOneField(
                        related_name="email_settings",
                        to="testcases.TestCase",
                        on_delete=models.CASCADE,
                    ),
                ),
                ("cc_list", models.TextField(default="")),
            ],
        ),
        migrations.CreateModel(
            name="TestCaseText",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("case_text_version", models.IntegerField()),
                (
                    "create_date",
                    models.DateTimeField(auto_now_add=True, db_column="creation_ts"),
                ),
                ("action", models.TextField(blank=True)),
                ("effect", models.TextField(blank=True)),
                ("setup", models.TextField(blank=True)),
                ("breakdown", models.TextField(blank=True)),
                (
                    "author",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL,
                        db_column="who",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "case",
                    models.ForeignKey(
                        related_name="text",
                        to="testcases.TestCase",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ["case", "-case_text_version"],
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.AlterUniqueTogether(
            name="testcasetext",
            unique_together={("case", "case_text_version")},
        ),
        migrations.AlterUniqueTogether(
            name="testcaseplan",
            unique_together={("plan", "case")},
        ),
        migrations.AlterUniqueTogether(
            name="category",
            unique_together={("product", "name")},
        ),
        migrations.RunPython(forwards_add_initial_data, reverse_add_initial_data),
    ]
