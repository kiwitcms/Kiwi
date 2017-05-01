# -*- coding: utf-8 -*-

import unittest

from django import test
from django.forms import ValidationError

from fields import MultipleEmailField
from forms import CaseTagForm
from tcms.testcases.models import TestCaseBugSystem
from tcms.tests import BasePlanCase
from tcms.tests.factories import ComponentFactory
from tcms.tests.factories import TestBuildFactory
from tcms.tests.factories import TestCaseComponentFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestCaseRunFactory
from tcms.tests.factories import TestCaseTagFactory
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import TestTagFactory


class TestMultipleEmailField(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestMultipleEmailField, cls).setUpClass()
        cls.default_delimiter = ','
        cls.field = MultipleEmailField(delimiter=cls.default_delimiter)

    def test_to_python(self):
        value = u'zhangsan@localhost'
        pyobj = self.field.to_python(value)
        self.assertEqual(pyobj, [value])

        value = u'zhangsan@localhost,,lisi@example.com,'
        pyobj = self.field.to_python(value)
        self.assertEqual(pyobj, [u'zhangsan@localhost', u'lisi@example.com'])

        for value in ('', None, []):
            pyobj = self.field.to_python(value)
            self.assertEqual(pyobj, [])

    def test_clean(self):
        value = u'zhangsan@localhost'
        data = self.field.clean(value)
        self.assertEqual(data, [value])

        value = u'zhangsan@localhost,lisi@example.com'
        data = self.field.clean(value)
        self.assertEqual(data, [u'zhangsan@localhost', u'lisi@example.com'])

        value = u',zhangsan@localhost, ,lisi@example.com, \n'
        data = self.field.clean(value)
        self.assertEqual(data, [u'zhangsan@localhost', 'lisi@example.com'])

        value = ',zhangsan,zhangsan@localhost, \n,lisi@example.com, '
        self.assertRaises(ValidationError, self.field.clean, value)

        value = ''
        self.field.required = True
        self.assertRaises(ValidationError, self.field.clean, value)

        value = ''
        self.field.required = False
        data = self.field.clean(value)
        self.assertEqual(data, [])


class TestCaseRemoveBug(BasePlanCase):
    """Test TestCase.remove_bug"""

    @classmethod
    def setUpTestData(cls):
        super(TestCaseRemoveBug, cls).setUpTestData()
        cls.build = TestBuildFactory(product=cls.product)
        cls.test_run = TestRunFactory(product_version=cls.version, plan=cls.plan,
                                      manager=cls.tester, default_tester=cls.tester)
        cls.case_run = TestCaseRunFactory(assignee=cls.tester, tested_by=cls.tester,
                                          case=cls.case, run=cls.test_run, build=cls.build)
        cls.bug_system = TestCaseBugSystem.objects.get(name='Bugzilla')

    def setUp(self):
        self.bug_id_1 = '12345678'
        self.case.add_bug(self.bug_id_1, self.bug_system.pk,
                          summary='error when add a bug to a case')
        self.bug_id_2 = '10000'
        self.case.add_bug(self.bug_id_2, self.bug_system.pk, case_run=self.case_run)

    def tearDown(self):
        self.case.case_bug.all().delete()

    def test_remove_case_bug(self):
        self.case.remove_bug(self.bug_id_1)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_1).exists()
        self.assertFalse(bug_found)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_2).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_2))

    def test_case_bug_not_removed_by_passing_case_run(self):
        self.case.remove_bug(self.bug_id_1, run_id=self.case_run.pk)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_1).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_1))

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_2).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_2))

    def test_remove_case_run_bug(self):
        self.case.remove_bug(self.bug_id_2, run_id=self.case_run.pk)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_2).exists()
        self.assertFalse(bug_found)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_1).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_1))

    def test_case_run_bug_not_removed_by_missing_case_run(self):
        self.case.remove_bug(self.bug_id_2)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_1).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_1))

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_2).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_2))


class TestCaseRemoveComponent(BasePlanCase):
    """Test TestCase.remove_component"""

    @classmethod
    def setUpTestData(cls):
        super(TestCaseRemoveComponent, cls).setUpTestData()

        cls.component_1 = ComponentFactory(name='Application',
                                           product=cls.product,
                                           initial_owner=cls.tester,
                                           initial_qa_contact=cls.tester)
        cls.component_2 = ComponentFactory(name='Database',
                                           product=cls.product,
                                           initial_owner=cls.tester,
                                           initial_qa_contact=cls.tester)

        cls.cc_rel_1 = TestCaseComponentFactory(case=cls.case, component=cls.component_1)
        cls.cc_rel_2 = TestCaseComponentFactory(case=cls.case, component=cls.component_2)

    def test_remove_a_component(self):
        self.case.remove_component(self.component_1)

        found = self.case.component.filter(pk=self.component_1.pk).exists()
        self.assertFalse(
            found, 'Component {0} exists. But, it should be removed.'.format(self.component_1.pk))
        found = self.case.component.filter(pk=self.component_2.pk).exists()
        self.assertTrue(
            found,
            'Component {0} does not exist. It should not be removed.'.format(self.component_2.pk))


class TestCaseRemovePlan(BasePlanCase):
    """Test TestCase.remove_plan"""

    @classmethod
    def setUpTestData(cls):
        super(TestCaseRemovePlan, cls).setUpTestData()

        cls.new_case = TestCaseFactory(author=cls.tester, default_tester=None, reviewer=cls.tester,
                                       plan=[cls.plan])

    def test_remove_plan(self):
        self.new_case.remove_plan(self.plan)

        found = self.plan.case.filter(pk=self.new_case.pk).exists()
        self.assertFalse(
            found, 'Case {0} should has no relationship to plan {0} now.'.format(self.new_case.pk,
                                                                                 self.plan.pk))


class TestCaseRemoveTag(BasePlanCase):
    """Test TestCase.remove_tag"""

    @classmethod
    def setUpTestData(cls):
        super(TestCaseRemoveTag, cls).setUpTestData()

        cls.tag_rhel = TestTagFactory(name='rhel')
        cls.tag_fedora = TestTagFactory(name='fedora')
        TestCaseTagFactory(case=cls.case, tag=cls.tag_rhel, user=cls.tester.pk)
        TestCaseTagFactory(case=cls.case, tag=cls.tag_fedora, user=cls.tester.pk)

    def test_remove_tag(self):
        self.case.remove_tag(self.tag_rhel)

        tag_pks = list(self.case.tag.all().values_list('pk', flat=True))
        self.assertEqual([self.tag_fedora.pk], tag_pks)


class CaseTagFormTest(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.tag_1 = TestTagFactory(name='tag one')
        cls.tag_2 = TestTagFactory(name='tag two')
        cls.tag_3 = TestTagFactory(name='tag three')

        cls.cases = []
        for i in range(5):
            case = TestCaseFactory(summary='test_case_number_%d' % i)
            case.add_tag(cls.tag_1)
            if i % 2 == 0:
                case.add_tag(cls.tag_2)
            if i % 3 == 0:
                case.add_tag(cls.tag_3)
            cls.cases.append(case)

    def test_populate_from_cases_contains_all_three_tags(self):
        case_ids = [case.pk for case in self.cases]
        form = CaseTagForm()
        form.populate(case_ids=case_ids)

        self.assertEqual(3, len(form.fields['o_tag'].queryset))
        form_tags = form.fields['o_tag'].queryset.values_list('name', flat=True)
        self.assertIn(self.tag_1.name, form_tags)
        self.assertIn(self.tag_2.name, form_tags)
        self.assertIn(self.tag_3.name, form_tags)
