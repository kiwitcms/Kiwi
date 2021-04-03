# -*- coding: utf-8 -*-
from collections import namedtuple

import vinaigrette
from colorfield.fields import ColorField
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.core.history import KiwiHistoricalRecords
from tcms.core.models.base import UrlMixin

TestExecutionStatusSubtotal = namedtuple(
    "TestExecutionStatusSubtotal",
    [
        "CompletedPercentage",
        "FailurePercentage",
        "SuccessPercentage",
    ],
)


class TestRun(models.Model, UrlMixin):
    history = KiwiHistoricalRecords()

    start_date = models.DateTimeField(db_index=True, null=True, blank=True)
    stop_date = models.DateTimeField(null=True, blank=True, db_index=True)
    planned_start = models.DateTimeField(db_index=True, null=True, blank=True)
    planned_stop = models.DateTimeField(db_index=True, null=True, blank=True)

    summary = models.TextField()
    notes = models.TextField(blank=True)

    plan = models.ForeignKey(
        "testplans.TestPlan", related_name="run", on_delete=models.CASCADE
    )
    build = models.ForeignKey(
        "management.Build", related_name="build_run", on_delete=models.CASCADE
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="manager", on_delete=models.CASCADE
    )
    default_tester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="default_tester",
        on_delete=models.CASCADE,
    )

    tag = models.ManyToManyField(
        "management.Tag", through="testruns.TestRunTag", related_name="run"
    )

    cc = models.ManyToManyField(settings.AUTH_USER_MODEL, through="testruns.TestRunCC")

    def __str__(self):
        return self.summary

    def _get_absolute_url(self):
        return reverse(
            "testruns-get",
            args=[
                self.pk,
            ],
        )

    def get_absolute_url(self):
        return self._get_absolute_url()

    def get_notify_addrs(self):
        """
        Get the all related mails from the run
        """
        send_to = [self.manager.email]
        send_to.extend(self.cc.values_list("email", flat=True))
        if self.default_tester_id:
            send_to.append(self.default_tester.email)

        for execution in self.executions.select_related("assignee").all():
            if execution.assignee_id:
                send_to.append(execution.assignee.email)

        send_to = set(send_to)
        # don't email author of last change
        send_to.discard(
            getattr(
                self.history.latest().history_user,  # pylint: disable=no-member
                "email",
                "",
            )
        )
        return list(send_to)

    def create_execution(
        self,
        case,
        assignee=None,
        build=None,
        sortkey=0,
    ):
        assignee = (
            assignee
            or (case.default_tester_id and case.default_tester)
            or (self.default_tester_id and self.default_tester)
        )

        return self.executions.create(
            case=case,
            assignee=assignee,
            tested_by=None,
            # usually IDLE but users can customize statuses
            status=TestExecutionStatus.objects.filter(weight=0).first(),
            case_text_version=case.history.latest().history_id,
            build=build or self.build,
            sortkey=sortkey,
            stop_date=None,
            start_date=None,
        )

    def add_tag(self, tag):
        return TestRunTag.objects.get_or_create(run=self, tag=tag)

    def add_cc(self, user):
        return TestRunCC.objects.get_or_create(
            run=self,
            user=user,
        )

    def remove_tag(self, tag):
        TestRunTag.objects.filter(run=self, tag=tag).delete()

    def remove_cc(self, user):
        TestRunCC.objects.filter(run=self, user=user).delete()

    @override("en")
    def stats_executions_status(self):
        """
        Get statistics based on executions' status

        :return: the statistics including the number of each status mapping,
                 total number of executions, complete percent, and failure percent.
        :rtype: namedtuple
        """
        total_count = self.executions.count()
        if total_count:
            complete_count = self.executions.exclude(status__weight=0).count()
            complete_percent = complete_count * 100.0 / total_count

            failing_count = self.executions.filter(status__weight__lt=0).count()
            failing_percent = failing_count * 100.0 / total_count
        else:
            complete_percent = 0.0
            failing_percent = 0.0

        return TestExecutionStatusSubtotal(
            complete_percent,
            failing_percent,
            complete_percent - failing_percent,
        )


class TestExecutionStatus(models.Model, UrlMixin):
    class Meta:
        # used in the admin view
        verbose_name_plural = _("Test execution statuses")

    name = models.CharField(max_length=60, blank=True, unique=True)
    weight = models.IntegerField(default=0)
    icon = models.CharField(max_length=64)
    color = ColorField()

    def __str__(self):
        return self.name


# register model for DB translations
vinaigrette.register(TestExecutionStatus, ["name"])


class TestExecution(models.Model, UrlMixin):
    history = KiwiHistoricalRecords()

    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="execution_assignee",
        on_delete=models.CASCADE,
    )
    tested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="execution_tester",
        on_delete=models.CASCADE,
    )
    case_text_version = models.IntegerField()
    start_date = models.DateTimeField(null=True, blank=True, db_index=True)
    stop_date = models.DateTimeField(null=True, blank=True, db_index=True)
    sortkey = models.IntegerField(null=True, blank=True)

    run = models.ForeignKey(
        TestRun, related_name="executions", on_delete=models.CASCADE
    )
    case = models.ForeignKey(
        "testcases.TestCase", related_name="executions", on_delete=models.CASCADE
    )
    status = models.ForeignKey(TestExecutionStatus, on_delete=models.CASCADE)
    build = models.ForeignKey("management.Build", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("case", "run", "case_text_version")

    def __str__(self):
        return "%s: %s" % (self.pk, self.case_id)

    def links(self):
        return LinkReference.objects.filter(execution=self.pk)

    def get_bugs(self):
        return self.links().filter(is_defect=True)

    def _get_absolute_url(self):
        # NOTE: this returns the URL to the TestRun containing this TestExecution!
        return reverse("testruns-get", args=[self.run_id])

    @property
    def actual_duration(self):
        if self.stop_date is None or self.start_date is None:
            return None
        return self.stop_date - self.start_date


class TestRunTag(models.Model):
    tag = models.ForeignKey("management.Tag", on_delete=models.CASCADE)
    run = models.ForeignKey(TestRun, related_name="tags", on_delete=models.CASCADE)


class TestRunCC(models.Model):
    run = models.ForeignKey(TestRun, related_name="cc_list", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("run", "user")
