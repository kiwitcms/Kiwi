# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from uuslug import slugify

from tcms.core.history import KiwiHistoricalRecords
from tcms.core.models import TCMSActionModel
from tcms.management.models import Version
from tcms.rpc.serializer import TestPlanRPCSerializer
from tcms.rpc.utils import distinct_filter
from tcms.testcases.models import TestCasePlan


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

    def get_absolute_url(self):
        return self._get_absolute_url()

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

        :param name: New name of cloned plan. If not passed, make_cloned_name is called
            to generate a default one.
        :type name: str
        :param product: Product of cloned plan. If not passed, original plan's product is used.
        :type product: :class:`tcms.management.models.Product`
        :param version: Product version of cloned plan. If not passed use from source plan.
        :type version: :class:`tcms.management.models.Version`
        :param new_author: New author of cloned plan. If not passed, original plan's
            author is used.
        :type new_author: settings.AUTH_USER_MODEL
        :param set_parent: Whether to set original plan as parent of cloned plan.
            Default is False.
        :type set_parent: bool
        :param copy_testcases: Whether to copy cases to cloned plan instead of just
            linking them. Default is False.
        :type copy_testcases: bool
        :param _kwargs: Unused catch-all variable container for any extra input
            which may be present
        :return: cloned plan
        :rtype: :class:`tcms.testplans.models.TestPlan`
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
        for tc_src in self.case.all():
            # this parameter should really be named clone_testcases b/c if set
            # it clones the source TC and then adds it to the new TP
            if copy_testcases:
                tc_src.clone(new_author, [tp_dest])
            else:
                # otherwise just link the existing TC to the new TP
                tp_dest.add_case(tc_src)

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
