# -*- coding: utf-8 -*-
import unittest
from tcms.core.templatetags.report_tags import percentage


class TestReportTagPercentage(unittest.TestCase):

    def test_percentage_calculation(self):

        self.assertEqual(percentage(5.0, 2.5), '200.0%')
        with self.assertRaises(ValueError):
            percentage('five', 'ten')
        self.assertEqual('0.0%', percentage(0, 2.0))
        self.assertEqual('0%', percentage(2.0, 0))
        self.assertEqual(percentage(1, 1), '100.0%')
        self.assertEqual(percentage(1, 3), '33.3%')
