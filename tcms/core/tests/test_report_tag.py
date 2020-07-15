# -*- coding: utf-8 -*-
import unittest
from tcms.core.templatetags.report_tags import percentage


class TestReportTagPercentage(unittest.TestCase):

    def test_percentage_calculation(self):

        with self.assertRaises(ValueError):
            percentage('five', 'ten')
        self.assertEqual('0.0%', percentage(0, 2.0))
        self.assertEqual('0%', percentage(2.0, 0))
        self.assertEqual(percentage(1, 1), '100.0%')
        self.assertEqual(percentage(1, 3), '33.3%')
        self.assertEqual(percentage(4.5, 4), '112.5%')
