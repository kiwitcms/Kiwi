# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

from django import test
from django.db.models import ObjectDoesNotExist

import tcms.rpc.utils as U
from tcms.tests.factories import ProductFactory


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
