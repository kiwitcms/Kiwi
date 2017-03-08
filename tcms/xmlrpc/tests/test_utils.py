# -*- coding: utf-8 -*-

import unittest

from django import test
from django.db.models import ObjectDoesNotExist

from tcms.tests.factories import ProductFactory
import tcms.xmlrpc.utils as U


class TestParseBool(unittest.TestCase):

    def test_parse_bool_value_with_rejected_args(self):
        rejected_args = (3, -1, "", "True", "False", "yes", "no", "33", "-11",
                         [], (), {}, None)
        for arg in rejected_args:
            self.assertRaisesRegexp(ValueError, 'Unacceptable bool value.',
                                    U.parse_bool_value, arg)

    def test_parse_bool_value(self):
        self.assertFalse(U.parse_bool_value(0))
        self.assertFalse(U.parse_bool_value('0'))
        self.assertFalse(U.parse_bool_value(False))

        self.assertTrue(U.parse_bool_value(1))
        self.assertTrue(U.parse_bool_value('1'))
        self.assertTrue(U.parse_bool_value(True))


class TestPreCheckProduct(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(name='World Of Warcraft')

    def test_pre_check_product_with_dict(self):
        product = U.pre_check_product({"product": self.product.pk})
        self.assertEqual(product.name, "World Of Warcraft")

        product = U.pre_check_product({"product": "World Of Warcraft"})
        self.assertEqual(product.name, "World Of Warcraft")

    def test_pre_check_product_with_no_key(self):
        self.assertRaises(ValueError, U.pre_check_product, {})

    def test_pre_check_product_with_illegal_types(self):
        types = ((), [], True, False, self,)
        for arg in types:
            self.assertRaisesRegexp(ValueError, 'The type of product is not recognizable.',
                                    U.pre_check_product, arg)

    def test_pre_check_product_with_number(self):
        product = U.pre_check_product(self.product.pk)
        self.assertEqual(product.name, "World Of Warcraft")

        self.assertRaises(ObjectDoesNotExist, U.pre_check_product, str(self.product.pk))

    def test_pre_check_product_with_name(self):
        product = U.pre_check_product("World Of Warcraft")
        self.assertEqual(product.name, "World Of Warcraft")

    def test_pre_check_product_with_no_exist(self):
        self.assertRaises(ObjectDoesNotExist, U.pre_check_product, {"product": 9999})
        self.assertRaises(ObjectDoesNotExist, U.pre_check_product, {"product": "unknown name"})


class TestPreProcessIds(unittest.TestCase):

    def test_pre_process_ids_with_list(self):
        ids = U.pre_process_ids(["1", "2", "3"])
        self.assertEqual(ids, [1, 2, 3])

    def test_pre_process_ids_with_str(self):
        ids = U.pre_process_ids("1")
        self.assertEqual(ids, [1])

        ids = U.pre_process_ids("1,2,3,4")
        self.assertEqual(ids, [1, 2, 3, 4])

    def test_pre_process_ids_with_int(self):
        ids = U.pre_process_ids(1)
        self.assertEqual(ids, [1])

    def test_pre_process_ids_with_others(self):
        self.assertRaisesRegexp(TypeError, 'Unrecognizable type of ids',
                                U.pre_process_ids, (1,))

        self.assertRaisesRegexp(TypeError, 'Unrecognizable type of ids',
                                U.pre_process_ids, {'a': 1})

    def test_pre_process_ids_with_string(self):
        self.assertRaises(ValueError, U.pre_process_ids, ["a", "b"])
        self.assertRaises(ValueError, U.pre_process_ids, "1@2@3@4")


class TestEstimatedTime(unittest.TestCase):

    def test_pre_process_estimated_time(self):
        bad_args = ([], (), {}, True, False, 0, 1, -1)
        for arg in bad_args:
            self.assertRaisesRegexp(ValueError, 'Invaild estimated_time format.',
                                    U.pre_process_estimated_time, arg)

    def test_pre_process_estimated_time_with_empty(self):
        time = U.pre_process_estimated_time("")
        self.assertEqual('', time)

    def test_pre_process_estimated_time_with_bad_form(self):
        self.assertRaisesRegexp(ValueError, 'Invaild estimated_time format.',
                                U.pre_process_estimated_time, "aaaaaa")

    def test_pre_process_estimated_time_with_time_string(self):
        time = U.pre_process_estimated_time("13:22:54")
        self.assertEqual(time, "13h22m54s")

        time = U.pre_process_estimated_time("1d13h22m54s")
        self.assertEqual(time, "1d13h22m54s")

    def test_pre_process_estimated_time_with_upper_string(self):
        self.assertRaisesRegexp(ValueError, 'Invaild estimated_time format.',
                                U.pre_process_estimated_time, "1D13H22M54S")

    def test_pre_process_estimated_time_with_string(self):
        self.assertRaisesRegexp(ValueError, 'Invaild estimated_time format.',
                                U.pre_process_estimated_time, "aa:bb:cc")

    def test_pre_process_estimated_time_with_mhs(self):
        self.assertRaisesRegexp(ValueError, 'Invaild estimated_time format.',
                                U.pre_process_estimated_time, "ambhcs")

    def test_pre_process_estimated_time_with_symbols(self):
        self.assertRaisesRegexp(ValueError, 'Invaild estimated_time format.',
                                U.pre_process_estimated_time, "aa@bb@cc")
