# -*- coding: utf-8 -*-

from datetime import datetime

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Max
from django.urls import reverse
from django.shortcuts import get_object_or_404

from uuslug import slugify

from tcms.core.models import TCMSActionModel
from tcms.core.utils.checksum import checksum
from tcms.management.models import Version
from tcms.testcases.models import TestCase
from tcms.testcases.models import Category
from tcms.testcases.models import TestCasePlan
from tcms.testcases.models import TestCaseStatus


class PlanType(TCMSActionModel):
    id = models.AutoField(db_column='type_id', primary_key=True)
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = u'test_plan_types'
        ordering = ['name']


class TestPlan(TCMSActionModel):
    """A plan within the TCMS"""

    plan_id = models.AutoField(max_length=11, primary_key=True)
    name = models.CharField(max_length=255, db_index=True)
    create_date = models.DateTimeField(db_column='creation_date', auto_now_add=True)
    is_active = models.BooleanField(db_column='isactive', default=True, db_index=True)
    extra_link = models.CharField(max_length=1024, default=None, blank=True, null=True)

    product_version = models.ForeignKey(Version, related_name='plans', on_delete=models.CASCADE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                              related_name='myplans', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('management.Product', related_name='plan',
                                on_delete=models.CASCADE)
    type = models.ForeignKey(PlanType, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', blank=True, null=True, related_name='child_set',
                               on_delete=models.CASCADE)

    env_group = models.ManyToManyField('management.EnvGroup', through='EnvPlanMap')
    tag = models.ManyToManyField('management.Tag',
                                 through='testplans.TestPlanTag',
                                 related_name='plan')

    class Meta:
        db_table = u'test_plans'
        index_together = [['product', 'plan_id']]

    def __str__(self):
        return self.name

    @classmethod
    def to_xmlrpc(cls, query=None):
        from tcms.xmlrpc.serializer import TestPlanXMLRPCSerializer
        from tcms.xmlrpc.utils import distinct_filter

        _query = query or {}
        qs = distinct_filter(TestPlan, _query).order_by('pk')
        serializer = TestPlanXMLRPCSerializer(model_class=cls, queryset=qs)
        return serializer.serialize_queryset()

    @classmethod
    def list(cls, query=None):
        """docstring for list_plans"""
        from django.db.models import Q

        new_query = {}

        for key, value in query.items():
            if value and key not in ['action', 't', 'f', 'a']:
                new_query[key] = value.strip() if hasattr(value, 'strip') else value

        query_set = cls.objects

        if new_query.get('search'):
            query_set = query_set.filter(Q(plan_id__icontains=new_query['search']) |
                                         Q(name__icontains=new_query['search']))
            del new_query['search']

        return query_set.filter(**new_query).order_by('pk').distinct()

    def confirmed_case(self):
        return self.case.filter(case_status__name='CONFIRMED')

    def latest_text(self):
        try:
            return self.text.select_related('author').order_by(
                '-plan_text_version')[0]
        except IndexError:
            return None
        except ObjectDoesNotExist:
            return None

    def text_exist(self):
        try:
            return self.text.exists()
        except IndexError:
            return False
        except ObjectDoesNotExist:
            return False

    def text_checksum(self):
        try:
            return self.text.order_by('-plan_text_version').only(
                'checksum')[0].checksum
        except IndexError:
            return None
        except ObjectDoesNotExist:
            return None

    def add_text(self,
                 author,
                 plan_text,
                 create_date=datetime.now(),
                 plan_text_version=None,
                 text_checksum=None):
        if not plan_text_version:
            latest_text = self.latest_text()
            if latest_text:
                plan_text_version = latest_text.plan_text_version + 1
            else:
                plan_text_version = 1

        if not text_checksum:
            old_checksum = self.text_checksum()
            new_checksum = checksum(plan_text)
            if old_checksum == new_checksum:
                return self.latest_text()

        return self.text.create(
            plan_text_version=plan_text_version,
            author=author,
            create_date=create_date,
            plan_text=plan_text,
            checksum=text_checksum or checksum(plan_text)
        )

    def add_case(self, case, sortkey=0):

        tcp, is_created = TestCasePlan.objects.get_or_create(
            plan=self,
            case=case,
        )
        if is_created:
            tcp.sortkey = sortkey
            tcp.save()

    def add_env_group(self, env_group):
        # Create the env plan map
        return EnvPlanMap.objects.create(
            plan=self,
            group=env_group,
        )

    def add_tag(self, tag):
        return TestPlanTag.objects.get_or_create(
            plan=self,
            tag=tag
        )

    def remove_tag(self, tag):
        TestPlanTag.objects.filter(plan=self, tag=tag).delete()

    def clear_env_groups(self):
        # Remove old env groups because we only maintanence on group per plan.
        return EnvPlanMap.objects.filter(plan=self).delete()

    def delete_case(self, case):
        TestCasePlan.objects.filter(case=case.pk, plan=self.pk).delete()

    def _get_absolute_url(self):
        return reverse('test_plan_url', args=[self.plan_id, slugify(self.name)])

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

    def clone(self, new_name=None, product=None, version=None,
              new_original_author=None, set_parent=True,
              copy_texts=True, default_text_author=None,
              copy_environment_group=True,
              link_cases=True, copy_cases=None,
              new_case_author=None,
              new_case_default_tester=None,
              default_component_initial_owner=None):
        """Clone this plan

        :param str new_name: New name of cloned plan. If not passed, make_cloned_name is called
            to generate a default one.
        :param product: Product of cloned plan. If not passed, original plan's product is used.
        :param version: Product version of cloned plan. If not passed, original plan's
            product_version is used.
        :param new_original_author: New author of cloned plan. If not passed, original plan's
            author is used.
        :param bool set_parent: Whether to set original plan as parent of cloned plan.
            Set by default.
        :param bool copy_texts: Whether to copy the four text. Copy by default.
        :param default_text_author: When not copy the four text, new text will be created.
            This is the default author of new created text.
        :param bool copy_environment_group: Whether to copy environment groups. Copy by default.
        :param bool link_cases: Whether to link cases to cloned plan. Default is True.
        :param bool copy_cases: Whether to copy cases to cloned plan instead of just linking them.
            Default is False.
        :param new_case_author: The author of copied cases. Used only if copy cases.
        :param new_case_default_tester: The default tester of copied cases. Used only if copy cases.
        :param default_component_initial_owner: Used only if copy cases. If copied case does not
            have original case' component, create it and use this value as the initial_owner.
        :rtype: cloned plan
        """

        if not copy_texts and not default_text_author:
            raise ValueError('Missing default text author when not copy texts.')

        if not copy_cases and not default_component_initial_owner:
            raise ValueError('Missing default component initial owner when not copy cases.')

        tp_dest = TestPlan.objects.create(
            name=new_name or self.make_cloned_name(),
            product=product or self.product,
            author=new_original_author or self.author,
            type=self.type,
            product_version=version or self.product_version,
            create_date=self.create_date,
            is_active=self.is_active,
            extra_link=self.extra_link,
            parent=self if set_parent else None)

        # Copy the plan documents
        if copy_texts:
            tptxts_src = self.text.all()
            for tptxt_src in tptxts_src:
                tp_dest.add_text(
                    plan_text_version=tptxt_src.plan_text_version,
                    author=tptxt_src.author,
                    create_date=tptxt_src.create_date,
                    plan_text=tptxt_src.plan_text)
        else:
            tp_dest.add_text(author=default_text_author, plan_text='')

        # Copy the plan tags
        for tp_tag_src in self.tag.all():
            tp_dest.add_tag(tag=tp_tag_src)

        # Copy the environment group
        if copy_environment_group:
            for env_group in self.env_group.all():
                tp_dest.add_env_group(env_group=env_group)

        # Link the cases of the plan
        if link_cases:
            tpcases_src = self.case.all()

            if copy_cases:
                for tpcase_src in tpcases_src:
                    tcp = get_object_or_404(TestCasePlan, plan=self, case=tpcase_src)
                    author = new_case_author or tpcase_src.author
                    default_tester = new_case_default_tester or tpcase_src.default_tester

                    tc_category, _ = Category.objects.get_or_create(
                        name=tpcase_src.category.name, product=product)

                    tpcase_dest = TestCase.objects.create(
                        create_date=tpcase_src.create_date,
                        is_automated=tpcase_src.is_automated,
                        script=tpcase_src.script,
                        arguments=tpcase_src.arguments,
                        summary=tpcase_src.summary,
                        requirement=tpcase_src.requirement,
                        alias=tpcase_src.alias,
                        estimated_time=tpcase_src.estimated_time,
                        case_status=TestCaseStatus.get_PROPOSED(),
                        category=tc_category,
                        priority=tpcase_src.priority,
                        author=author,
                        default_tester=default_tester)

                    # Add case to plan.
                    tp_dest.add_case(tpcase_dest, tcp.sortkey)

                    for tc_tag_src in tpcase_src.tag.all():
                        tpcase_dest.add_tag(tag=tc_tag_src)

                    for component in tpcase_src.component.filter(product__id=self.product_id):
                        try:
                            new_c = tp_dest.product.component.get(name=component.name)
                        except ObjectDoesNotExist:
                            new_c = tp_dest.product.component.create(
                                name=component.name,
                                initial_owner=default_component_initial_owner,
                                description=component.description)

                        tpcase_dest.add_component(new_c)

                    text = tpcase_src.latest_text()

                    if text:
                        tpcase_dest.add_text(author=text.author,
                                             action=text.action,
                                             effect=text.effect,
                                             setup=text.setup,
                                             breakdown=text.breakdown,
                                             create_date=text.create_date)
            else:
                for tpcase_src in tpcases_src:
                    tcp = get_object_or_404(TestCasePlan, plan=self, case=tpcase_src)
                    tp_dest.add_case(tpcase_src, tcp.sortkey)

        return tp_dest


class TestPlanText(TCMSActionModel):
    plan = models.ForeignKey(TestPlan, related_name='text', on_delete=models.CASCADE)
    plan_text_version = models.IntegerField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, db_column='who', on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True,
                                       db_column='creation_ts')
    plan_text = models.TextField(blank=True)
    checksum = models.CharField(max_length=64)

    class Meta:
        db_table = u'test_plan_texts'
        ordering = ['plan', '-plan_text_version']
        unique_together = ('plan', 'plan_text_version')


class TestPlanTag(models.Model):
    tag = models.ForeignKey('management.Tag', on_delete=models.CASCADE)
    plan = models.ForeignKey(TestPlan, on_delete=models.CASCADE)
    user = models.IntegerField(default="1", db_column='userid')

    class Meta:
        db_table = u'test_plan_tags'


class TestPlanEmailSettings(models.Model):
    plan = models.OneToOneField(TestPlan, related_name='email_settings', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    auto_to_plan_owner = models.BooleanField(default=False)
    auto_to_plan_author = models.BooleanField(default=False)
    auto_to_case_owner = models.BooleanField(default=False)
    auto_to_case_default_tester = models.BooleanField(default=False)
    notify_on_plan_update = models.BooleanField(default=False)
    notify_on_case_update = models.BooleanField(default=False)


class EnvPlanMap(models.Model):
    plan = models.ForeignKey(TestPlan, on_delete=models.CASCADE)
    group = models.ForeignKey('management.EnvGroup', on_delete=models.CASCADE)

    class Meta:
        db_table = u'tcms_env_plan_map'
