# -*- coding: utf-8 -*-

from tcms.testcases.models import TestCase
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestRun


class SmartDjangoQuery:
    """
    Class mainly wraps the look-up rules and priorities\n
    of fields that should be applied on Django queryset.\n
    Mind the priorities cause they make difference about efficiency.
    """

    # where in the form, by specifying a fieldname named
    # FIELDNAME_EXCLUDE_POSTFIX, then this field will be used to exclude the
    # relevant results from queryset
    EXCLUDE_POSTFIX = 'exclude'

    CONTENT_TYPES = {
        TestRun.__name__: TestRun,
        TestPlan.__name__: TestPlan,
        TestCase.__name__: TestCase,
    }

    PRIORITIES = {
        TestPlan.__name__: (
            'pl_id', 'pl_authors', 'pl_owners', 'pl_product', 'pl_component',
            'pl_type', 'pl_version', 'pl_summary',
            'pl_active', 'pl_created_since', 'pl_created_before', 'pl_tags'),
        TestCase.__name__: (
            'cs_id', 'cs_authors', 'cs_tester', 'cs_product', 'cs_component',
            'cs_tags', 'cs_bugs', 'cs_proposed', 'cs_priority',
            'cs_created_since', 'cs_status', 'cs_auto', 'cs_created_before',
            'cs_category', 'cs_summary', 'cs_script'),
        TestRun.__name__: (
            'r_id', 'r_product', 'r_manager', 'r_tester', 'r_real_tester',
            'r_assginee', 'r_build', 'r_version', 'r_running', 'r_tags', 'r_env',
            'r_created_since', 'r_created_before', 'r_summary',)
    }

    RULES = {
        TestPlan.__name__: {
            'pl_id': 'pk__in',
            'pl_summary': 'name__icontains',
            'pl_type': 'type__in',
            'pl_authors': 'author__username__in',
            'pl_owners': 'owner__username__in',
            'pl_tags': 'tag__name__in',
            'pl_tags_distinct': True,
            'pl_active': 'is_active',
            'pl_created_since': 'create_date__gte',
            'pl_created_before': 'create_date__lte',
            'pl_product': 'product__id__in',
            'pl_component': 'component__in',
            'pl_component_distinct': True,
            'pl_version': 'product_version__in',
        },
        TestCase.__name__: {
            'cs_id': 'pk__in',
            'cs_summary': 'summary__icontains',
            'cs_authors': 'author__username__in',
            'cs_tester': 'default_tester__username__in',
            'cs_tags': 'tag__name__in',
            'cs_tags_distinct': True,
            'cs_bugs': 'case_bug__bug_id__in',
            'cs_bugs_distinct': True,
            'cs_status': 'case_status__in',
            'cs_auto': 'is_automated',
            'cs_proposed': 'is_automated_proposed',
            'cs_priority': 'priority__in',
            'cs_script': 'script__search',
            'cs_created_since': 'create_date__gte',
            'cs_created_before': 'create_date__lte',
            'cs_component': 'component__in',
            'cs_component_distinct': True,
            'cs_category': 'category__in',
            'cs_product': 'category__product__in',
        },
        TestRun.__name__: {
            'r_id': 'pk__in',
            'r_summary': 'summary__icontains',
            'r_manager': 'manager__username__in',
            'r_assignee': 'case_run__assignee__username__in',
            'r_tester': 'default_tester__username__in',
            'r_running': 'stop_date__isnull',
            'r_tags': 'tag__name__in',
            'r_tags_distinct': True,
            'r_env': 'env_value__value__in',
            'r_env_distinct': True,
            'r_created_since': 'start_date__gte',
            'r_created_before': 'start_date__lte',
            'r_real_tester': 'case_run__tested_by__username__in',
            'r_real_tester_distinct': True,
            'r_product': 'build__product__in',
            'r_build': 'build__in',
            'r_version': 'product_version__in'
        }
    }

    def __init__(self, queries, result_kls):
        self.queryset = self.CONTENT_TYPES[result_kls].objects.all()
        self.queries = queries
        self.result_kls = result_kls

    def filter(self):
        queryset = None
        rules = self.RULES[self.result_kls]
        for key in self.PRIORITIES[self.result_kls]:
            if key not in rules:
                continue
            lookup = rules[key]
            value = self.queries.get(key, None)
            if isinstance(value, (bool, int)) or value:
                if queryset is None:
                    queryset = self.queryset
                if self.queries.get(key + '_' + self.EXCLUDE_POSTFIX, False):
                    # for complicated Q filtering
                    queryset = queryset.exclude(**{lookup: value})
                else:
                    queryset = queryset.filter(**{lookup: value})

                if rules.get(key + '_distinct', False):
                    queryset = queryset.distinct()

        self.queryset = queryset

    def evaluate(self):
        self.filter()
        return self.queryset
