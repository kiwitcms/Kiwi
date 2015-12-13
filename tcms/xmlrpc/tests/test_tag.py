# -*- coding: utf-8 -*-
from xmlrpclib import Fault

from django_nose.testcases import FastFixtureTestCase

from tcms.xmlrpc.api import tag


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


class TestTag(FastFixtureTestCase):
    fixtures = ['unittest.json']

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

    def test_get_tags_with_id(self):
        try:
            test_tag = tag.get_tags(None, {
                'ids': [1]
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            print test_tag
            self.assertIsNotNone(test_tag)
            self.assertEqual(len(test_tag), 1)
            self.assertEqual(test_tag[0]['id'], 1)
            self.assertEqual(test_tag[0]['name'], 'QWER')

        try:
            test_tag = tag.get_tags(None, {
                'ids': [4, 5, 6]
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(test_tag)
            self.assertEqual(len(test_tag), 3)
            self.assertEqual(test_tag[0]['id'], 4)
            self.assertEqual(test_tag[0]['name'], 'P')
            self.assertEqual(test_tag[1]['id'], 5)
            self.assertEqual(test_tag[1]['name'], 'Z')
            self.assertEqual(test_tag[2]['id'], 6)
            self.assertEqual(test_tag[2]['name'], 'VS')

    def test_get_tags_with_name(self):
        try:
            test_tag = tag.get_tags(None, {
                'names': ['QWER']
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(test_tag)
            self.assertEqual(test_tag[0]['id'], 1)
            self.assertEqual(test_tag[0]['name'], 'QWER')

        try:
            test_tag = tag.get_tags(None, {
                'names': ['R1', 'R2', 'R3']
            })
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(test_tag)
            self.assertEqual(test_tag[0]['id'], 11)
            self.assertEqual(test_tag[0]['name'], 'R1')
            self.assertEqual(test_tag[1]['id'], 12)
            self.assertEqual(test_tag[1]['name'], 'R2')
            self.assertEqual(test_tag[2]['id'], 13)
            self.assertEqual(test_tag[2]['name'], 'R3')

    def test_get_tags_with_non_exist_fields(self):
        try:
            tag.get_tags(None, {
                'tag_id': [1]
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_tags_with_non_list(self):
        try:
            tag.get_tags(None, {
                'ids': 1
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            tag.get_tags(None, {
                'names': 'QWER'
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)
