# -*- coding: utf-8 -*-

import unittest

from tcms.core.ajax import strip_parameters


class TestStripParameters(unittest.TestCase):

    def setUp(self):
        self.request_dict = {
            'name__startswith': 'something',
            'info_type': 'tags',
            'format': 'ulli',
            'case__plan': 1,
            'field': 'tag__name',
        }
        self.internal_parameters = ('info_type', 'field', 'format')

    def test_remove_parameters_in_dict(self):
        simplified_dict = strip_parameters(self.request_dict, self.internal_parameters)
        for p in self.internal_parameters:
            self.assertFalse(p in simplified_dict)

        self.assertEqual('something', simplified_dict['name__startswith'])
        self.assertEqual(1, simplified_dict['case__plan'])

    def test_remove_parameters_not_in_dict(self):
        simplified_dict = strip_parameters(self.request_dict, ['non-existing-parameter'])
        self.assertEqual(self.request_dict, simplified_dict)
