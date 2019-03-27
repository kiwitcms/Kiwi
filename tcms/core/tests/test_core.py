# -*- coding: utf-8 -*-

import unittest

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

        self.assertEqual([1], string_to_list(1))

        self.assertEqual([], string_to_list(()))

        strings = 'abcdefg'
        result = string_to_list(strings)
        self.assertEqual([strings], result)

        strings = u'abcdefg'
        result = string_to_list(strings)
        self.assertEqual([strings], result)

        strings = 'abcdefg'
        result = string_to_list(strings, ':')
        self.assertEqual([strings], result)
