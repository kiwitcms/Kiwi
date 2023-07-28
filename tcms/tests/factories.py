# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods, unused-argument

import factory
from django.conf import settings
from django.db.models import signals
from django.utils import timezone
from factory.django import DjangoModelFactory

from tcms.management.models import Priority
from tcms.testcases.models import TestCaseStatus
from tcms.testruns.models import TestExecutionStatus


class UserFactory(DjangoModelFactory):
    class Meta:
        model = settings.AUTH_USER_MODEL

    username = factory.Sequence(lambda n: f"User{n}")
    email = factory.LazyAttribute(lambda user: f"{user.username}@example.com")
    is_staff = True

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for group in extracted:
                self.groups.add(group)  # pylint: disable=no-member


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = "auth.Group"

    name = factory.Sequence(lambda n: f"Group {n}")


# ### Factories for app management ###


class ClassificationFactory(DjangoModelFactory):
    class Meta:
        model = "management.Classification"

    name = factory.Sequence(lambda n: f"Classification {n}")


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = "management.Product"

    name = factory.Sequence(lambda n: f"Product {n}")
    classification = factory.SubFactory(ClassificationFactory)


class PriorityFactory(DjangoModelFactory):
    class Meta:
        model = "management.Priority"

    value = factory.Sequence(lambda n: f"P{n}")
    is_active = True


class ComponentFactory(DjangoModelFactory):
    class Meta:
        model = "management.Component"

    name = factory.Sequence(lambda n: f"Component {n}")
    product = factory.SubFactory(ProductFactory)
    initial_owner = factory.SubFactory(UserFactory)
    initial_qa_contact = factory.SubFactory(UserFactory)


class VersionFactory(DjangoModelFactory):
    class Meta:
        model = "management.Version"

    value = factory.Sequence(lambda n: f"0.{n}")
    product = factory.SubFactory(ProductFactory)


class BuildFactory(DjangoModelFactory):
    class Meta:
        model = "management.Build"

    name = factory.Sequence(lambda n: f"Build {n}")
    version = factory.SubFactory(VersionFactory)


class TagFactory(DjangoModelFactory):
    class Meta:
        model = "management.Tag"

    name = factory.Sequence(lambda n: f"Tag {n}")


class PlanTypeFactory(DjangoModelFactory):
    class Meta:
        model = "testplans.PlanType"

    name = factory.Sequence(lambda n: f"Plan type {n}")


class TestPlanFactory(DjangoModelFactory):
    class Meta:
        model = "testplans.TestPlan"

    name = factory.Sequence(lambda n: f"Plan name {n}")
    text = factory.Sequence(lambda n: f"Plan document {n}")
    create_date = factory.LazyFunction(timezone.now)
    product_version = factory.SubFactory(VersionFactory)
    author = factory.SubFactory(UserFactory)
    product = factory.SubFactory(ProductFactory)
    type = factory.SubFactory(PlanTypeFactory)

    @factory.post_generation
    def tag(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                TestPlanTagFactory(plan=self, tag=tag)


class TestPlanTagFactory(DjangoModelFactory):
    class Meta:
        model = "testplans.TestPlanTag"

    plan = factory.SubFactory(TestPlanFactory)
    tag = factory.SubFactory(TagFactory)


class TestPlanEmailSettingsFactory(DjangoModelFactory):
    class Meta:
        model = "testplans.TestPlanEmailSettings"

    plan = factory.SubFactory(TestPlanFactory)


# ### Factories for app testcases ###


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = "testcases.Category"

    name = factory.Sequence(lambda n: f"category {n}")
    product = factory.SubFactory(ProductFactory)
    description = ""


@factory.django.mute_signals(signals.post_save)
class TestCaseFactory(DjangoModelFactory):
    class Meta:
        model = "testcases.TestCase"

    summary = factory.Sequence(lambda n: f"Test case summary {n}")
    case_status = factory.LazyFunction(lambda: TestCaseStatus.objects.all()[0:1][0])
    priority = factory.LazyFunction(lambda: Priority.objects.all()[0:1][0])
    category = factory.SubFactory(CategoryFactory)
    author = factory.SubFactory(UserFactory)
    default_tester = factory.SubFactory(UserFactory)
    reviewer = factory.SubFactory(UserFactory)
    text = factory.Sequence(lambda n: f"Given-When-Then {n}")

    @factory.post_generation
    def plan(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for plan in extracted:
                TestCasePlanFactory(case=self, plan=plan)

    @factory.post_generation
    def component(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for component in extracted:
                TestCaseComponentFactory(case=self, component=component)

    @factory.post_generation
    def tag(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                TestCaseTagFactory(case=self, tag=tag)


class TestCasePlanFactory(DjangoModelFactory):
    class Meta:
        model = "testcases.TestCasePlan"

    plan = factory.SubFactory(TestPlanFactory)
    case = factory.SubFactory(TestCaseFactory)
    sortkey = factory.Sequence(lambda n: n)


class TestCaseComponentFactory(DjangoModelFactory):
    class Meta:
        model = "testcases.TestCaseComponent"

    case = factory.SubFactory(TestCaseFactory)
    component = factory.SubFactory(ComponentFactory)


class TestCaseTagFactory(DjangoModelFactory):
    class Meta:
        model = "testcases.TestCaseTag"

    case = factory.SubFactory(TestCaseFactory)
    tag = factory.SubFactory(TagFactory)


class TestCaseEmailSettingsFactory(DjangoModelFactory):
    class Meta:
        model = "testcases.TestCaseEmailSettings"

    case = factory.SubFactory(TestCaseFactory)


# ### Factories for apps testruns ###
class TestRunFactory(DjangoModelFactory):
    class Meta:
        model = "testruns.TestRun"

    summary = factory.Sequence(lambda n: f"Test run summary {n}")
    stop_date = None
    notes = ""
    plan = factory.SubFactory(TestPlanFactory)
    build = factory.SubFactory(BuildFactory)
    manager = factory.SubFactory(UserFactory)
    default_tester = factory.SubFactory(UserFactory)

    @factory.post_generation
    def tag(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                TestRunTagFactory(run=self, tag=tag)

    @factory.post_generation
    def cc(self, create, extracted, **kwargs):  # pylint: disable=invalid-name
        if not create:
            return
        if extracted:
            for user in extracted:
                TestRunCCFactory(run=self, user=user)


def text_version_from_history(obj):
    if obj.case.history.count():
        return obj.case.history.latest().history_id

    return 0


class TestExecutionFactory(DjangoModelFactory):
    class Meta:
        model = "testruns.TestExecution"

    assignee = factory.SubFactory(UserFactory)
    tested_by = factory.SubFactory(UserFactory)
    stop_date = None
    start_date = None
    sortkey = factory.Sequence(lambda n: n)
    run = factory.SubFactory(TestRunFactory)
    case = factory.SubFactory(TestCaseFactory)
    case_text_version = factory.LazyAttribute(text_version_from_history)
    status = factory.LazyFunction(
        lambda: TestExecutionStatus.objects.order_by("pk").first()
    )
    build = factory.SubFactory(BuildFactory)


class LinkReferenceFactory(DjangoModelFactory):
    class Meta:
        model = "linkreference.LinkReference"

    execution = factory.SubFactory(TestExecutionFactory)
    name = factory.Sequence(lambda n: f"Bug {n}")
    url = factory.Sequence(lambda n: f"https://example.com/link/{n}/")
    is_defect = True


class TestRunTagFactory(DjangoModelFactory):
    class Meta:
        model = "testruns.TestRunTag"

    tag = factory.SubFactory(TagFactory)
    run = factory.SubFactory(TestRunFactory)


class TestRunCCFactory(DjangoModelFactory):
    class Meta:
        model = "testruns.TestRunCC"

    run = factory.SubFactory(TestRunFactory)
    user = factory.SubFactory(UserFactory)
