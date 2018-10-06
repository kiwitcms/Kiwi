# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

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
        for arg in [(), [], self]:
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
