# -*- coding: utf-8 -*-

import unittest

from django_nose.testcases import FastFixtureTestCase

from tcms.testcases.models import TestCase
from tcms.core.db import GroupByResult

from tcms.core.utils import string_to_list


class TestUtilsFunctions(unittest.TestCase):

    def test_string_to_list(self):
        strings = 'Python,Go,,Perl,Ruby'
        strings_list = ['Python', 'Go', 'Perl', 'Ruby']
        strings_list.sort()
        expected_strings = [u'Python', u'Go', u'Perl', u'Ruby']
        expected_strings.sort()

        result = string_to_list(strings_list)
        result.sort()
        self.assertEqual(expected_strings, result)

        result = string_to_list(strings)
        result.sort()
        self.assertEqual(expected_strings, result)

        another_strings = strings.replace(',', '#')
        result = string_to_list(another_strings, '#')
        result.sort()
        self.assertEqual(expected_strings, result)

        strings = 1
        self.assertRaises(AttributeError, string_to_list, strings)

        strings = ()
        self.assertRaises(AttributeError, string_to_list, strings)

        strings = 'abcdefg'
        result = string_to_list(strings)
        self.assertEqual([strings], result)

        strings = u'abcdefg'
        result = string_to_list(strings)
        self.assertEqual([strings], result)

        strings = 'abcdefg'
        result = string_to_list(strings, ':')
        self.assertEqual([strings], result)


class TestUtilsXmlrpc(FastFixtureTestCase):

    fixtures = ['unittest.json']

    def setUp(self):
        self.testcase_with_default_tester_null = TestCase.objects.extra(
            where=['default_tester_id is null'])[0:1].get()
        self.testcase_with_default_tester_0 = TestCase.objects.extra(
            where=['default_tester_id = 0'])[0:1].get()
        self.testcase_with_valid_default_tester = TestCase.objects.filter(
            default_tester__isnull=False)[0:1].get()

    def test_serialize_model_foreignkey(self):
        '''Testing whether the foreign key is serialized properly

        If foreign key has related object, the field should be serialized with
        the correct value.
        If there is no related object with the foreign key, both the field and
        the related object retrived via the relationship are set to None.
        '''

        from tcms.xmlrpc.serializer import XMLRPCSerializer

        s = XMLRPCSerializer(model=self.testcase_with_default_tester_null)
        result = s.serialize_model()
        self.assertEqual(result['default_tester'], None)
        self.assertEqual(result['default_tester_id'], None)

        s = XMLRPCSerializer(model=self.testcase_with_default_tester_0)
        result = s.serialize_model()
        self.assertEqual(result['default_tester'], None)
        self.assertEqual(result['default_tester_id'], None)

        s = XMLRPCSerializer(model=self.testcase_with_valid_default_tester)
        result = s.serialize_model()
        self.assertNotEqual(result['default_tester'], None)
        self.assertNotEqual(result['default_tester_id'], None)


class GroupByResultDictLikeTest(TestCase):
    '''Test dict like behaviors'''

    def setUp(self):
        self.groupby_result = GroupByResult({'total': 100})

    def test_in(self):
        self.assert_('a' not in self.groupby_result)
        self.assert_('total' in self.groupby_result)

    def test_key(self):
        self.assert_(self.groupby_result.keys(), ['total'])

    def test_setdefault(self):
        ret_val = self.groupby_result.setdefault('count', {})
        self.assertEqual(ret_val, {})

        ret_val = self.groupby_result.setdefault('total', 200)
        self.assertEqual(ret_val, 100)

    def test_getitem(self):
        ret_val = self.groupby_result['total']
        self.assertEqual(ret_val, 100)

        try:
            ret_val = self.groupby_result['xxx']
        except KeyError:
            pass
        else:
            self.fail('xxx does not exist. KeyError should be raised.')

    def test_setitem(self):
        self.groupby_result['count'] = 200
        self.assertEqual(self.groupby_result['count'], 200)

        self.groupby_result['total'] = 999
        self.assertEqual(self.groupby_result['total'], 999)

    def test_get(self):
        ret_val = self.groupby_result.get('total')
        self.assertEqual(ret_val, 100)

        ret_val = self.groupby_result.get('count', 999)
        self.assertEqual(ret_val, 999)

        ret_val = self.groupby_result.get('xxx')
        self.assertEqual(ret_val, None)

    def test_len(self):
        self.assertEqual(len(self.groupby_result), 1)

    def test_del(self):
        self.groupby_result['count'] = 200
        del self.groupby_result['total']
        self.assert_('total' not in self.groupby_result)
        del self.groupby_result['count']
        self.assert_('count' not in self.groupby_result)
        self.assertEqual(len(self.groupby_result), 0)


class GroupByResultCalculationTest(TestCase):
    '''Test calculation of GroupByResult'''

    def setUp(self):
        self.groupby_result = GroupByResult({
            1: 100,
            2: 300,
            4: 400,
        })

        self.nested_groupby_result = GroupByResult({
            1: GroupByResult({'a': 1,
                              'b': 2,
                              'c': 3}),
            2: GroupByResult({1: 1,
                              2: 2}),
            3: GroupByResult({'PASSED': 10,
                              'WAIVED': 20,
                              'FAILED': 30,
                              'PAUSED': 40}),
        })

    def _sample_total(self):
        return sum(count for key, count in self.groupby_result.iteritems())

    def _sample_nested_total(self):
        total = 0
        for key, nested_result in self.nested_groupby_result.iteritems():
            for n, count in nested_result.iteritems():
                total += count
        return total

    def test_total(self):
        total = self.groupby_result.total
        self.assertEqual(total, self._sample_total())

    def test_nested_total(self):
        total = self.nested_groupby_result.total
        self.assertEqual(total, self._sample_nested_total())


class GroupByResultLevelTest(TestCase):
    def setUp(self):
        self.levels_groupby_result = GroupByResult({
            'build_1': GroupByResult({
                'plan_1': GroupByResult({
                    'run_1': GroupByResult(
                        {'passed': 1, 'failed': 2, 'error': 3, }),
                    'run_2': GroupByResult(
                        {'passed': 1, 'failed': 2, 'error': 3, }),
                    'run_3': GroupByResult(
                        {'passed': 1, 'failed': 2, 'error': 3, }),
                }),
                'plan_2': GroupByResult({
                    'run_1': GroupByResult(
                        {'passed': 1, 'failed': 2, 'error': 3, }),
                    'run_2': GroupByResult(
                        {'passed': 1, 'failed': 2, 'error': 3, }),
                }),
            }),
            'build_2': GroupByResult({
                'plan_1': GroupByResult({
                    'run_1': GroupByResult(
                        {'passed': 1, 'failed': 2, 'error': 3, }),
                    'run_4': GroupByResult(
                        {'paused': 2, 'failed': 2, 'waived': 6, }),
                    'run_5': GroupByResult(
                        {'paused': 1, 'failed': 2, 'waived': 3, }),
                }),
                'plan_2': GroupByResult({
                    'run_1': GroupByResult(
                        {'passed': 1, 'failed': 2, 'error': 3, }),
                    'run_4': GroupByResult(
                        {'paused': 2, 'failed': 2, 'waived': 6, }),
                    'run_5': GroupByResult(
                        {'paused': 1, 'failed': 2, 'waived': 3, }),
                }),
            }),
        })

    def test_value_leaf_count(self):
        value_leaf_count = self.levels_groupby_result.leaf_values_count()
        self.assertEqual(value_leaf_count, 33)

        value_leaf_count = self.levels_groupby_result[
            'build_1'].leaf_values_count()
        self.assertEqual(value_leaf_count, 15)

        level_node = self.levels_groupby_result['build_2']['plan_2']
        value_leaf_count = level_node.leaf_values_count()
        self.assertEqual(value_leaf_count, 9)

    def test_value_leaf_in_row_count(self):
        value_leaf_count = self.levels_groupby_result.leaf_values_count(
            value_in_row=True)
        self.assertEqual(value_leaf_count, 11)

        level_node = self.levels_groupby_result['build_2']
        value_leaf_count = level_node.leaf_values_count(value_in_row=True)
        self.assertEqual(value_leaf_count, 6)

        level_node = self.levels_groupby_result['build_1']['plan_2']
        value_leaf_count = level_node.leaf_values_count(value_in_row=True)
        self.assertEqual(value_leaf_count, 2)
