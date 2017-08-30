# -*- coding: utf-8 -*-

from django import test
from django.urls import reverse


class TestInfo(test.TestCase):

    def test_lowercase_string_is_converted_to_bool(self):
        url = "%s?info_type=builds&product_id=1&is_active=true" % reverse('ajax-info')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
