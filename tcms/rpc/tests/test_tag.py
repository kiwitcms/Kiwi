# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

from tcms.rpc.tests.utils import APITestCase
from tcms.tests.factories import TagFactory


class Tag(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.tag_db = TagFactory(name='db')
        self.tag_fedora = TagFactory(name='fedora')
        self.tag_python = TagFactory(name='python')
        self.tag_tests = TagFactory(name='tests')
        self.tag_xmlrpc = TagFactory(name='xmlrpc')
        self.tags = [self.tag_db, self.tag_fedora, self.tag_python, self.tag_tests, self.tag_xmlrpc]

    def test_get_tags_with_ids(self):
        test_tag = self.rpc_client.Tag.filter({'id__in': [self.tag_python.pk,
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
        test_tag = self.rpc_client.Tag.filter({'name__in': ['python', 'fedora', 'db']})
        self.assertIsNotNone(test_tag)
        self.assertEqual(3, len(test_tag))

        test_tag = sorted(test_tag, key=lambda item: item['id'])
        self.assertEqual(test_tag[0]['id'], self.tag_db.pk)
        self.assertEqual(test_tag[0]['name'], 'db')
        self.assertEqual(test_tag[1]['id'], self.tag_fedora.pk)
        self.assertEqual(test_tag[1]['name'], 'fedora')
        self.assertEqual(test_tag[2]['id'], self.tag_python.pk)
        self.assertEqual(test_tag[2]['name'], 'python')
