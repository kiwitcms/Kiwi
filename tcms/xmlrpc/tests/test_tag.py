# -*- coding: utf-8 -*-

from xmlrpclib import Fault

from django import test
from tcms.xmlrpc.api import tag
from tcms.tests.factories import TestTagFactory


class AssertMessage(object):
    NOT_VALIDATE_ARGS = "Missing validations for args."
    NOT_VALIDATE_REQUIRED_ARGS = "Missing validations for required args."
    NOT_VALIDATE_ILLEGAL_ARGS = "Missing validations for illegal args."
    NOT_VALIDATE_FOREIGN_KEY = "Missing validations for foreign key."
    NOT_VALIDATE_LENGTH = "Missing validations for length of value."
    NOT_VALIDATE_URL_FORMAT = "Missing validations for URL format."

    SHOULD_BE_400 = "Error code should be 400."
    SHOULD_BE_409 = "Error code should be 409."
    SHOULD_BE_500 = "Error code should be 500."
    SHOULD_BE_403 = "Error code should be 403."
    SHOULD_BE_401 = "Error code should be 401."
    SHOULD_BE_404 = "Error code should be 404."
    SHOULD_BE_501 = "Error code should be 501."
    SHOULD_BE_1 = "Error code should be 1."

    UNEXCEPT_ERROR = "Unexcept error occurs."


class TestTag(test.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tag_db = TestTagFactory(name='db')
        cls.tag_fedora = TestTagFactory(name='fedora')
        cls.tag_python = TestTagFactory(name='python')
        cls.tag_tests = TestTagFactory(name='tests')
        cls.tag_xmlrpc = TestTagFactory(name='xmlrpc')
        cls.tags = [cls.tag_db, cls.tag_fedora, cls.tag_python, cls.tag_tests, cls.tag_xmlrpc]

    @classmethod
    def tearDownClass(cls):
        for t in cls.tags:
            t.delete()

    def test_get_tags_with_no_args(self):
        bad_args = (None, [], {}, ())
        for arg in bad_args:
            try:
                tag.get_tags(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_tags_with_illgel_args(self):
        bad_args = (1, 0, -1, True, False, '', 'aaaa', object)
        for arg in bad_args:
            try:
                tag.get_tags(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_tags_with_ids(self):
        try:
            test_tag = tag.get_tags(None, {'ids': [self.tag_python.pk,
                                                   self.tag_db.pk,
                                                   self.tag_fedora.pk]})
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(test_tag)
            self.assertEqual(3, len(test_tag))

            test_tag = sorted(test_tag, key=lambda item: item['id'])
            self.assertEqual(test_tag[0]['id'], self.tag_db.pk)
            self.assertEqual(test_tag[0]['name'], 'db')
            self.assertEqual(test_tag[1]['id'], self.tag_fedora.pk)
            self.assertEqual(test_tag[1]['name'], 'fedora')
            self.assertEqual(test_tag[2]['id'], self.tag_python.pk)
            self.assertEqual(test_tag[2]['name'], 'python')

    def test_get_tags_with_names(self):
        try:
            test_tag = tag.get_tags(None, {'names': ['python', 'fedora', 'db']})
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(test_tag)
            self.assertEqual(3, len(test_tag))

            test_tag = sorted(test_tag, key=lambda item: item['id'])
            self.assertEqual(test_tag[0]['id'], self.tag_db.pk)
            self.assertEqual(test_tag[0]['name'], 'db')
            self.assertEqual(test_tag[1]['id'], self.tag_fedora.pk)
            self.assertEqual(test_tag[1]['name'], 'fedora')
            self.assertEqual(test_tag[2]['id'], self.tag_python.pk)
            self.assertEqual(test_tag[2]['name'], 'python')

    def test_get_tags_with_non_exist_fields(self):
        try:
            tag.get_tags(None, {'tag_id': [1]})
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_tags_with_non_list(self):
        try:
            tag.get_tags(None, {'ids': 1})
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)
