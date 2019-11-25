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

# ### Factories for app management ###


class UserFactory(DjangoModelFactory):

    class Meta:
        model = settings.AUTH_USER_MODEL

    username = factory.Sequence(lambda n: 'User%d' % n)
    email = factory.LazyAttribute(lambda user: '%s@example.com' % user.username)
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
        model = 'auth.Group'

    name = factory.Sequence(lambda n: 'Group %d' % n)


# ### Factories for app management ###


class ClassificationFactory(DjangoModelFactory):

    class Meta:
        model = 'management.Classification'

    name = factory.Sequence(lambda n: 'Classification %d' % n)


class ProductFactory(DjangoModelFactory):

    class Meta:
        model = 'management.Product'

    name = factory.Sequence(lambda n: 'Product %d' % n)
    classification = factory.SubFactory(ClassificationFactory)


class PriorityFactory(DjangoModelFactory):

    class Meta:
        model = 'management.Priority'

    value = factory.Sequence(lambda n: 'P%d' % n)
    is_active = True


class ComponentFactory(DjangoModelFactory):

    class Meta:
        model = 'management.Component'

    name = factory.Sequence(lambda n: 'Component %d' % n)
    product = factory.SubFactory(ProductFactory)
    initial_owner = factory.SubFactory(UserFactory)
    initial_qa_contact = factory.SubFactory(UserFactory)


class VersionFactory(DjangoModelFactory):

    class Meta:
        model = 'management.Version'

    value = factory.Sequence(lambda n: '0.%d' % n)
    product = factory.SubFactory(ProductFactory)


class BuildFactory(DjangoModelFactory):

    class Meta:
        model = 'management.Build'

    name = factory.Sequence(lambda n: 'Build %d' % n)
    product = factory.SubFactory(ProductFactory)


class TagFactory(DjangoModelFactory):

    class Meta:
        model = 'management.Tag'

    name = factory.Sequence(lambda n: 'Tag %d' % n)


class PlanTypeFactory(DjangoModelFactory):

    class Meta:
        model = 'testplans.PlanType'

    name = factory.Sequence(lambda n: 'Plan type %d' % n)


class TestPlanFactory(DjangoModelFactory):

    class Meta:
        model = 'testplans.TestPlan'

    name = factory.Sequence(lambda n: 'Plan name %d' % n)
    text = factory.Sequence(lambda n: 'Plan document %d' % n)
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
        model = 'testplans.TestPlanTag'

    plan = factory.SubFactory(TestPlanFactory)
    tag = factory.SubFactory(TagFactory)


class TestPlanEmailSettingsFactory(DjangoModelFactory):

    class Meta:
        model = 'testplans.TestPlanEmailSettings'

    plan = factory.SubFactory(TestPlanFactory)


# ### Factories for app testcases ###


class CategoryFactory(DjangoModelFactory):

    class Meta:
        model = 'testcases.Category'

    name = factory.Sequence(lambda n: 'category %d' % n)
    product = factory.SubFactory(ProductFactory)
    description = ''


@factory.django.mute_signals(signals.post_save)
class TestCaseFactory(DjangoModelFactory):

    class Meta:
        model = 'testcases.TestCase'

    summary = factory.Sequence(lambda n: 'Test case summary %d' % n)
    case_status = factory.LazyFunction(lambda: TestCaseStatus.objects.all()[0:1][0])
    priority = factory.LazyFunction(lambda: Priority.objects.all()[0:1][0])
    category = factory.SubFactory(CategoryFactory)
    author = factory.SubFactory(UserFactory)
    default_tester = factory.SubFactory(UserFactory)
    reviewer = factory.SubFactory(UserFactory)
    text = factory.Sequence(lambda n: 'Given-When-Then %d' % n)

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
        model = 'testcases.TestCasePlan'

    plan = factory.SubFactory(TestPlanFactory)
    case = factory.SubFactory(TestCaseFactory)
    sortkey = factory.Sequence(lambda n: n)


class TestCaseComponentFactory(DjangoModelFactory):

    class Meta:
        model = 'testcases.TestCaseComponent'

    case = factory.SubFactory(TestCaseFactory)
    component = factory.SubFactory(ComponentFactory)


class TestCaseTagFactory(DjangoModelFactory):

    class Meta:
        model = 'testcases.TestCaseTag'

    case = factory.SubFactory(TestCaseFactory)
    tag = factory.SubFactory(TagFactory)


class TestCaseEmailSettingsFactory(DjangoModelFactory):

    class Meta:
        model = 'testcases.TestCaseEmailSettings'

    case = factory.SubFactory(TestCaseFactory)


# ### Factories for apps testruns ###
class TestRunFactory(DjangoModelFactory):

    class Meta:
        model = 'testruns.TestRun'

    summary = factory.Sequence(lambda n: 'Test run summary %d' % n)
    product_version = factory.SubFactory(VersionFactory)
    stop_date = None
    notes = ''
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


class TestExecutionFactory(DjangoModelFactory):

    class Meta:
        model = 'testruns.TestExecution'

    assignee = factory.SubFactory(UserFactory)
    tested_by = factory.SubFactory(UserFactory)
    case_text_version = factory.LazyAttribute(lambda obj: obj.case.history.latest().history_id)
    close_date = None
    sortkey = factory.Sequence(lambda n: n)
    run = factory.SubFactory(TestRunFactory)
    case = factory.SubFactory(TestCaseFactory)
    status = factory.LazyFunction(lambda: TestExecutionStatus.objects.order_by('pk').first())
    build = factory.SubFactory(BuildFactory)


class LinkReferenceFactory(DjangoModelFactory):

    class Meta:
        model = 'linkreference.LinkReference'

    execution = factory.SubFactory(TestExecutionFactory)
    name = factory.Sequence(lambda n: "Bug %d" % n)
    url = factory.Sequence(lambda n: "https://example.com/link/%d/" % n)
    is_defect = True


class TestRunTagFactory(DjangoModelFactory):

    class Meta:
        model = 'testruns.TestRunTag'

    tag = factory.SubFactory(TagFactory)
    run = factory.SubFactory(TestRunFactory)


class TestRunCCFactory(DjangoModelFactory):

    class Meta:
        model = 'testruns.TestRunCC'

    run = factory.SubFactory(TestRunFactory)
    user = factory.SubFactory(UserFactory)
