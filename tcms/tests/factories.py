# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods, unused-argument

from datetime import datetime

from django.db.models import signals

import factory
from factory.django import DjangoModelFactory

from tcms.management.models import Priority
from tcms.testcases.models import TestCaseStatus
from tcms.testcases.models import BugSystem
from tcms.testruns.models import TestCaseRunStatus


# ### Factories for app management ###


class UserFactory(DjangoModelFactory):

    class Meta:
        model = 'auth.User'

    username = factory.Sequence(lambda n: 'User%d' % n)
    email = factory.LazyAttribute(lambda user: '%s@example.com' % user.username)

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for group in extracted:
                self.groups.add(group)


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


class EnvGroupFactory(DjangoModelFactory):

    class Meta:
        model = 'management.EnvGroup'

    name = factory.Sequence(lambda n: 'Env group %d' % n)

    @factory.post_generation
    def property(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for property in extracted:
                EnvGroupPropertyMapFactory(group=self, property=property)


class EnvPropertyFactory(DjangoModelFactory):

    class Meta:
        model = 'management.EnvProperty'

    name = factory.Sequence(lambda n: 'Env property %d' % n)


class EnvGroupPropertyMapFactory(DjangoModelFactory):

    class Meta:
        model = 'management.EnvGroupPropertyMap'

    group = factory.SubFactory(EnvGroupFactory)
    property = factory.SubFactory(EnvPropertyFactory)


class EnvValueFactory(DjangoModelFactory):

    class Meta:
        model = 'management.EnvValue'

    value = factory.Sequence(lambda n: 'Env value %d' % n)
    property = factory.SubFactory(EnvPropertyFactory)


# ### Factories for app testplans ###


class PlanTypeFactory(DjangoModelFactory):

    class Meta:
        model = 'testplans.PlanType'

    name = factory.Sequence(lambda n: 'Plan type %d' % n)


class TestPlanFactory(DjangoModelFactory):

    class Meta:
        model = 'testplans.TestPlan'

    name = factory.Sequence(lambda n: 'Plan name %d' % n)
    create_date = factory.LazyFunction(datetime.now)
    product_version = factory.SubFactory(VersionFactory)
    owner = factory.SubFactory(UserFactory)
    author = factory.SubFactory(UserFactory)
    product = factory.SubFactory(ProductFactory)
    type = factory.SubFactory(PlanTypeFactory)
    # FIXME: How to create field for field parent

    @factory.post_generation
    def env_group(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for group in extracted:
                EnvPlanMapFactory(plan=self, group=group)

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


class EnvPlanMapFactory(DjangoModelFactory):

    class Meta:
        model = 'testplans.EnvPlanMap'

    plan = factory.SubFactory(TestPlanFactory)
    group = factory.SubFactory(EnvGroupFactory)


class TestPlanTextFactory(DjangoModelFactory):

    class Meta:
        model = 'testplans.TestPlanText'

    plan = factory.SubFactory(TestPlanFactory)
    author = factory.SubFactory(UserFactory)
    create_date = factory.LazyFunction(datetime.now)
    plan_text = factory.Sequence(lambda n: 'Plan text %d' % n)


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
    user = 0


class TestCaseTextFactory(DjangoModelFactory):

    class Meta:
        model = 'testcases.TestCaseText'

    case = factory.SubFactory(TestCaseFactory)
    case_text_version = 1
    author = factory.SubFactory(UserFactory)
    action = 'action'
    effect = 'effect'
    setup = 'setup'
    breakdown = 'breakdown'


class BugFactory(DjangoModelFactory):

    class Meta:
        model = 'testcases.Bug'

    bug_id = '12345678'
    summary = factory.LazyAttribute(lambda obj: 'Summary of bug %s' % obj.bug_id)
    description = ''
    bug_system = factory.LazyFunction(lambda: BugSystem.objects.all()[0:1][0])
    case_run = factory.SubFactory('tests.TestCaseRunFactory')
    case = factory.SubFactory(TestCaseFactory)


class ContactFactory(DjangoModelFactory):

    class Meta:
        model = 'testcases.Contact'

    name = factory.Sequence(lambda n: 'contact_%d' % n)
    email = factory.LazyAttribute(lambda obj: '%s@example.com' % obj.name.replace(' ', '_'))


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
    # FIXME: field name build conflicts with method Factory.build
    build = factory.SubFactory(BuildFactory)
    manager = factory.SubFactory(UserFactory)
    default_tester = factory.SubFactory(UserFactory)

    @factory.post_generation
    def env_group(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for value in extracted:
                EnvRunValueMapFactory(run=self, value=value)

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


class TestCaseRunFactory(DjangoModelFactory):

    class Meta:
        model = 'testruns.TestCaseRun'

    assignee = factory.SubFactory(UserFactory)
    tested_by = factory.SubFactory(UserFactory)
    case_text_version = 1
    running_date = None
    close_date = None
    notes = ''
    sortkey = factory.Sequence(lambda n: n)
    run = factory.SubFactory(TestRunFactory)
    case = factory.SubFactory(TestCaseFactory)
    case_run_status = factory.LazyFunction(lambda: TestCaseRunStatus.objects.order_by('pk').first())
    build = factory.SubFactory(BuildFactory)


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


class EnvRunValueMapFactory(DjangoModelFactory):

    class Meta:
        model = 'testruns.EnvRunValueMap'

    run = factory.SubFactory(TestRunFactory)
    value = factory.SubFactory(EnvValueFactory)


# ### Factories for app profiles ###

class UserProfileFactory(DjangoModelFactory):

    class Meta:
        model = 'profiles.UserProfile'

    user = factory.SubFactory(UserFactory)
