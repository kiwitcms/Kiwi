# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.urls import reverse
from uuslug import slugify

from tcms.core.history import KiwiHistoricalRecords
from tcms.core.models import TCMSActionModel
from tcms.management.models import Version
from tcms.testcases.models import (Category, TestCase, TestCasePlan,
                                   TestCaseStatus)

from tcms.rpc.serializer import TestPlanRPCSerializer
from tcms.rpc.utils import distinct_filter


class PlanType(TCMSActionModel):
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class TestPlan(TCMSActionModel):
    """A plan within the TCMS"""
    history = KiwiHistoricalRecords()

    name = models.CharField(max_length=255, db_index=True)
    text = models.TextField(blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, db_index=True)
    extra_link = models.CharField(max_length=1024, default=None, blank=True, null=True)

    product_version = models.ForeignKey(Version, related_name='plans', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('management.Product', related_name='plan',
                                on_delete=models.CASCADE)
    type = models.ForeignKey(PlanType, on_delete=models.CASCADE)
    parent = models.ForeignKey('TestPlan', blank=True, null=True, related_name='child_set',
                               on_delete=models.CASCADE)

    tag = models.ManyToManyField('management.Tag',
                                 through='testplans.TestPlanTag',
                                 related_name='plan')

    def __str__(self):
        return self.name

    @classmethod
    def to_xmlrpc(cls, query=None):

        _query = query or {}
        qs = distinct_filter(TestPlan, _query).order_by('pk')
        serializer = TestPlanRPCSerializer(model_class=cls, queryset=qs)
        return serializer.serialize_queryset()

    def add_case(self, case, sortkey=None):
        if sortkey is None:
            lastcase = self.testcaseplan_set.order_by('-sortkey').first()
            if lastcase and lastcase.sortkey is not None:
                sortkey = lastcase.sortkey + 10
            else:
                sortkey = 0

        return TestCasePlan.objects.get_or_create(
            plan=self,
            case=case,
            defaults={
                'sortkey': sortkey
            }
        )[0]

    def add_tag(self, tag):
        return TestPlanTag.objects.get_or_create(
            plan=self,
            tag=tag
        )

    def remove_tag(self, tag):
        TestPlanTag.objects.filter(plan=self, tag=tag).delete()

    def delete_case(self, case):
        TestCasePlan.objects.filter(case=case.pk, plan=self.pk).delete()

    def _get_absolute_url(self):
        return reverse('test_plan_url', args=[self.pk, slugify(self.name)])

    def get_case_sortkey(self):
        """
        Get case sortkey.
        """
        result = TestCasePlan.objects.filter(plan=self).aggregate(Max('sortkey'))
        sortkey = result['sortkey__max']
        if sortkey is None:
            return None
        return sortkey + 10

    def _get_email_conf(self):
        try:
            return self.email_settings
        except ObjectDoesNotExist:
            return TestPlanEmailSettings.objects.create(plan=self)

    emailing = property(_get_email_conf)

    def make_cloned_name(self):
        """Make default name of cloned plan"""
        return 'Copy of {}'.format(self.name)

    def clone(self, name=None, product=None, version=None,
              new_author=None, set_parent=False, copy_testcases=False, **_kwargs):
        """Clone this plan

        :param str name: New name of cloned plan. If not passed, make_cloned_name is called
            to generate a default one.
        :param product: Product of cloned plan. If not passed, original plan's product is used.
        :param version: Product version of cloned plan. If not passed use from source plan.
        :param new_author: New author of cloned plan. If not passed, original plan's
            author is used.
        :param bool set_parent: Whether to set original plan as parent of cloned plan.
            Default is False.
        :param bool copy_testcases: Whether to copy cases to cloned plan instead of just
            linking them. Default is False.
        :rtype: cloned plan
        """
        tp_dest = TestPlan.objects.create(
            name=name or self.make_cloned_name(),
            product=product or self.product,
            author=new_author or self.author,
            type=self.type,
            product_version=version or self.product_version,
            create_date=self.create_date,
            is_active=self.is_active,
            extra_link=self.extra_link,
            parent=self if set_parent else None,
            text=self.text)

        # Copy the plan tags
        for tp_tag_src in self.tag.all():
            tp_dest.add_tag(tag=tp_tag_src)

        # include TCs inside cloned TP
        for tpcase_src in self.case.all():
            tcp = get_object_or_404(TestCasePlan, plan=self, case=tpcase_src)

            if copy_testcases:
                # todo: create a function/method which clones the test cases instead of
                # duplicating the clone operation here and inside testcases.views.clone
                tc_category, _ = Category.objects.get_or_create(
                    name=tpcase_src.category.name, product=product)

                tpcase_dest = TestCase.objects.create(
                    create_date=tpcase_src.create_date,
                    is_automated=tpcase_src.is_automated,
                    script=tpcase_src.script,
                    arguments=tpcase_src.arguments,
                    summary=tpcase_src.summary,
                    requirement=tpcase_src.requirement,
                    case_status=TestCaseStatus.get_proposed(),
                    category=tc_category,
                    priority=tpcase_src.priority,
                    author=new_author,
                    default_tester=tpcase_src.default_tester,
                    text=tpcase_src.text)

                # Add case to plan.
                tp_dest.add_case(tpcase_dest, tcp.sortkey)

                for tc_tag_src in tpcase_src.tag.all():
                    tpcase_dest.add_tag(tag=tc_tag_src)

                for component in tpcase_src.component.filter(product_id=self.product_id):
                    try:
                        new_c = tp_dest.product.component.get(name=component.name)
                    except ObjectDoesNotExist:
                        new_c = tp_dest.product.component.create(
                            name=component.name,
                            initial_owner=new_author,
                            description=component.description)

                    tpcase_dest.add_component(new_c)
            else:
                tp_dest.add_case(tpcase_src, tcp.sortkey)

        return tp_dest


class TestPlanTag(models.Model):
    tag = models.ForeignKey('management.Tag', on_delete=models.CASCADE)
    plan = models.ForeignKey(TestPlan, on_delete=models.CASCADE)


class TestPlanEmailSettings(models.Model):
    plan = models.OneToOneField(TestPlan, related_name='email_settings', on_delete=models.CASCADE)
    auto_to_plan_author = models.BooleanField(default=True)
    auto_to_case_owner = models.BooleanField(default=True)
    auto_to_case_default_tester = models.BooleanField(default=True)
    notify_on_plan_update = models.BooleanField(default=True)
    notify_on_case_update = models.BooleanField(default=True)
