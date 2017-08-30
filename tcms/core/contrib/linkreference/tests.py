# -*- coding: utf-8 -*-

import unittest

from django.http import HttpResponse

from .forms import TargetCharField
from tcms.core.responses import (HttpJSONResponse,
                                 HttpJSONResponseBadRequest,
                                 HttpJSONResponseServerError)


class TestCustomResponses(unittest.TestCase):
    def test_HttpJSONResponse(self):
        resp = HttpJSONResponse(content='{}')

        self.assertTrue(isinstance(resp, HttpResponse))
        self.assertEqual(resp['content-type'], 'application/json')
        self.assertEqual(resp.status_code, 200)

    def test_HttpJSONResponseBadRequest(self):
        resp = HttpJSONResponseBadRequest(content='{}')

        self.assertTrue(isinstance(resp, HttpResponse))
        self.assertEqual(resp['content-type'], 'application/json')
        self.assertEqual(resp.status_code, 400)

    def test_HttpJSONResponseServerError(self):
        resp = HttpJSONResponseServerError(content='{}')

        self.assertTrue(isinstance(resp, HttpResponse))
        self.assertEqual(resp['content-type'], 'application/json')
        self.assertEqual(resp.status_code, 500)


class TestTargetCharField(unittest.TestCase):
    class PseudoClass(object):
        pass

    def setUp(self):
        test_targets = {'TestCaseRun': self.__class__.PseudoClass}
        self.field = TargetCharField(targets=test_targets)

    def test_type(self):
        from django.forms import Field

        self.assertTrue(isinstance(self.field, Field))

    def test_clean(self):
        url_argu_value = 'TestCaseRun'
        self.assertEqual(self.field.clean(url_argu_value),
                         self.__class__.PseudoClass)

        from django.forms import ValidationError

        url_argu_value = 'TestCase'
        self.assertRaises(ValidationError, self.field.clean, url_argu_value)


class LinkReferenceModel(unittest.TestCase):
    pass
