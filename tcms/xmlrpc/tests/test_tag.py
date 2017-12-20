# -*- coding: utf-8 -*-

from xmlrpc.client import Fault as XmlRPCFault

from tcms.tests.factories import TestTagFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestTag(XmlrpcAPIBaseTest):
    def _fixture_setup(self):
        super(TestTag, self)._fixture_setup()

        self.tag_db = TestTagFactory(name='db')
        self.tag_fedora = TestTagFactory(name='fedora')
        self.tag_python = TestTagFactory(name='python')
        self.tag_tests = TestTagFactory(name='tests')
        self.tag_xmlrpc = TestTagFactory(name='xmlrpc')
        self.tags = [self.tag_db, self.tag_fedora, self.tag_python, self.tag_tests, self.tag_xmlrpc]

    def test_get_tags_with_no_args(self):
        for param in [None, [], {}, (), 1, 0, -1, True, False, '', 'aaaa', object]:
            with self.assertRaisesRegex(XmlRPCFault, ".*Argument values must be a dictionary.*"):
                self.rpc_client.Tag.get_tags(None)

    def test_get_tags_with_ids(self):
        test_tag = self.rpc_client.Tag.get_tags({'ids': [self.tag_python.pk,
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
        test_tag = self.rpc_client.Tag.get_tags({'names': ['python', 'fedora', 'db']})
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
        with self.assertRaisesRegex(XmlRPCFault, ".*Must specify ids or names at least.*"):
            self.rpc_client.Tag.get_tags({'tag_id': [1]})

    def test_get_tags_with_non_list(self):
        with self.assertRaises(XmlRPCFault):
            self.rpc_client.Tag.get_tags({'ids': 1})
