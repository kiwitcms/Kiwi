# -*- coding: utf-8 -*-

from tcms.tests.factories import ProductFactory
from tcms.tests.factories import CategoryFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestCategory(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestCategory, self)._fixture_setup()

        self.product_nitrate = ProductFactory(name='nitrate')
        self.product_xmlrpc = ProductFactory(name='xmlrpc')
        self.case_categories = [
            CategoryFactory(name='auto', product=self.product_nitrate),
            CategoryFactory(name='manual', product=self.product_nitrate),
            CategoryFactory(name='pending', product=self.product_xmlrpc),
        ]

    def test_filter_by_name_and_product_id(self):
        cat = self.rpc_client.Category.filter({
            'name': 'manual',
            'product': self.product_nitrate.pk
        })[0]
        self.assertEqual(cat['name'], 'manual')

    def test_filter_by_product_id(self):
        cat = self.rpc_client.Category.filter({'product': self.product_nitrate.pk})
        self.assertIsNotNone(cat)

        # PostgreSQL returns data in arbitrary order
        category_names = [c['name'] for c in cat]

        self.assertEqual(3, len(category_names))
        self.assertIn('--default--', category_names)
        self.assertIn('auto', category_names)
        self.assertIn('manual', category_names)

    def test_filter_non_existing_doesnt_raise(self):
        found = self.rpc_client.Category.filter({'pk': -9})
        self.assertEqual(0, len(found))
