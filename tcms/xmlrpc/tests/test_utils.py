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
            try:
                U.parse_bool_value(arg)
            except ValueError as e:
                self.assertEqual(str(e), 'Unacceptable bool value.')
            else:
                self.fail("Missing validations for %s" % arg)

    def test_parse_bool_value(self):
        self.assertFalse(U.parse_bool_value(0))
        self.assertFalse(U.parse_bool_value('0'))
        self.assertFalse(U.parse_bool_value(False))

        self.assertTrue(U.parse_bool_value(1))
        self.assertTrue(U.parse_bool_value('1'))
        self.assertTrue(U.parse_bool_value(True))


class TestPreCheckProduct(test.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.product = ProductFactory(name='World Of Warcraft')

    @classmethod
    def tearDownClass(cls):
        cls.product.delete()
        cls.product.classification.delete()

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
            try:
                U.pre_check_product(arg)
            except ValueError as e:
                self.assertEqual(str(e), 'The type of product is not recognizable.')
            else:
                self.fail("Missing validations for %s" % arg)

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
        try:
            U.pre_process_ids((1,))
        except TypeError as e:
            self.assertEqual(str(e), 'Unrecognizable type of ids')
        else:
            self.fail("Missing validations.")

        try:
            U.pre_process_ids(dict(a=1))
        except TypeError as e:
            self.assertEqual(str(e), 'Unrecognizable type of ids')
        else:
            self.fail("Missing validations.")

    def test_pre_process_ids_with_string(self):
        try:
            U.pre_process_ids(["a", "b"])
        except ValueError:
            pass
        except Exception:
            self.fail("Unexcept error occurs.")
        else:
            self.fail("Missing validations.")

        try:
            U.pre_process_ids("1@2@3@4")
        except ValueError:
            pass
        except Exception:
            self.fail("Unexcept error occurs.")
        else:
            self.fail("Missing validations.")


class TestEstimatedTime(unittest.TestCase):

    def test_pre_process_estimated_time(self):
        bad_args = ([], (), {}, True, False, 0, 1, -1)
        for arg in bad_args:
            try:
                U.pre_process_estimated_time(arg)
            except ValueError as e:
                self.assertEqual(str(e), 'Invaild estimated_time format.')
            except Exception:
                self.fail("Unexcept error occurs.")
            else:
                self.fail("Missing validations.")

    def test_pre_process_estimated_time_with_empty(self):
        time = U.pre_process_estimated_time("")
        self.assertEqual('', time)

    def test_pre_process_estimated_time_with_bad_form(self):
        try:
            U.pre_process_estimated_time("aaaaaa")
        except ValueError as e:
            self.assertEqual(str(e), 'Invaild estimated_time format.')
        else:
            self.fail("Missing validations.")

    def test_pre_process_estimated_time_with_time_string(self):
        time = U.pre_process_estimated_time("13:22:54")
        self.assertEqual(time, "13h22m54s")

        time = U.pre_process_estimated_time("1d13h22m54s")
        self.assertEqual(time, "1d13h22m54s")

    def test_pre_process_estimated_time_with_upper_string(self):
        try:
            U.pre_process_estimated_time("1D13H22M54S")
        except ValueError as e:
            self.assertEqual(str(e), 'Invaild estimated_time format.')
        else:
            self.fail("Missing validations.")

    def test_pre_process_estimated_time_with_string(self):
        try:
            U.pre_process_estimated_time("aa:bb:cc")
        except ValueError as e:
            self.assertEqual(str(e), 'Invaild estimated_time format.')
        else:
            self.fail("Missing validations.")

    def test_pre_process_estimated_time_with_mhs(self):
        try:
            U.pre_process_estimated_time("ambhcs")
        except ValueError as e:
            self.assertEqual(str(e), 'Invaild estimated_time format.')
        else:
            self.fail("Missing validations.")

    def test_pre_process_estimated_time_with_symbols(self):
        try:
            U.pre_process_estimated_time("aa@bb@cc")
        except ValueError as e:
            self.assertEqual(str(e), 'Invaild estimated_time format.')
        else:
            self.fail("Missing validations.")
