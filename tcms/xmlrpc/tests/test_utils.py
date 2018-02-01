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
            with self.assertRaisesRegex(ValueError, 'Unacceptable bool value.'):
                U.parse_bool_value(arg)

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
        for arg in [(), [], True, False, self]:
            with self.assertRaisesRegex(ValueError, 'The type of product is not recognizable.'):
                U.pre_check_product(arg)

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


class TestEstimatedTime(unittest.TestCase):

    def test_pre_process_estimated_time(self):
        bad_args = ([], (), {})
        for arg in bad_args:
            with self.assertRaisesRegex(ValueError, 'Invalid estimated_time format.'):
                U.pre_process_estimated_time(arg)

    def test_pre_process_estimated_time_with_empty(self):
        time = U.pre_process_estimated_time("")
        self.assertEqual('', time)

    def test_pre_process_estimated_time_with_bad_form(self):
        with self.assertRaisesRegex(ValueError, 'Invalid estimated_time format.'):
            U.pre_process_estimated_time("aaaaaa")

    def test_pre_process_estimated_time_with_time_string(self):
        time = U.pre_process_estimated_time("13:22:54")
        self.assertEqual(time, "13h22m54s")

        time = U.pre_process_estimated_time("1d13h22m54s")
        self.assertEqual(time, "1d13h22m54s")

    def test_pre_process_estimated_time_with_upper_string(self):
        with self.assertRaisesRegex(ValueError, 'Invalid estimated_time format.'):
            U.pre_process_estimated_time("1D13H22M54S")

    def test_pre_process_estimated_time_with_string(self):
        with self.assertRaisesRegex(ValueError, 'Invalid estimated_time format.'):
            U.pre_process_estimated_time("aa:bb:cc")

    def test_pre_process_estimated_time_with_mhs(self):
        with self.assertRaisesRegex(ValueError, 'Invalid estimated_time format.'):
            U.pre_process_estimated_time("ambhcs")

    def test_pre_process_estimated_time_with_symbols(self):
        with self.assertRaisesRegex(ValueError, 'Invalid estimated_time format.'):
            U.pre_process_estimated_time("aa@bb@cc")
