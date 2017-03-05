# -*- coding: utf-8 -*-

from httplib import BAD_REQUEST

from tcms.xmlrpc.api import tag
from tcms.tests.factories import TestTagFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestTag(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.tag_db = TestTagFactory(name='db')
        cls.tag_fedora = TestTagFactory(name='fedora')
        cls.tag_python = TestTagFactory(name='python')
        cls.tag_tests = TestTagFactory(name='tests')
        cls.tag_xmlrpc = TestTagFactory(name='xmlrpc')
        cls.tags = [cls.tag_db, cls.tag_fedora, cls.tag_python, cls.tag_tests, cls.tag_xmlrpc]

    def test_get_tags_with_no_args(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, tag.get_tags, None, None)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, tag.get_tags, None, [])
        self.assertRaisesXmlrpcFault(BAD_REQUEST, tag.get_tags, None, {})
        self.assertRaisesXmlrpcFault(BAD_REQUEST, tag.get_tags, None, ())

    def test_get_tags_with_illgel_args(self):
        bad_args = (1, 0, -1, True, False, '', 'aaaa', object)
        for arg in bad_args:
            self.assertRaisesXmlrpcFault(BAD_REQUEST, tag.get_tags, None, arg)

    def test_get_tags_with_ids(self):
        test_tag = tag.get_tags(None, {'ids': [self.tag_python.pk,
                                               self.tag_db.pk,
                                               self.tag_fedora.pk]})
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
        test_tag = tag.get_tags(None, {'names': ['python', 'fedora', 'db']})
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
        self.assertRaisesXmlrpcFault(BAD_REQUEST, tag.get_tags, None, {'tag_id': [1]})

    def test_get_tags_with_non_list(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, tag.get_tags, None, {'ids': 1})
