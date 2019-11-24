# -*- coding: utf-8 -*-

from tcms.management.models import Tag
from tcms.tests import (LoggedInTestCase, remove_perm_from_user,
                        user_should_have_perm)
from tcms.tests.factories import TagFactory


class TestTagsWithPermission(LoggedInTestCase):
    """Test Tag usage/autocreation"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        user_should_have_perm(cls.tester, 'management.add_tag')

        cls.existing_tag = TagFactory()

    def test_get_existing_tag(self):
        tag, created = Tag.get_or_create(self.tester, self.existing_tag.name)

        self.assertEqual(tag.pk, self.existing_tag.pk)
        self.assertFalse(created)

    def test_autocreate_new_tag(self):
        tag, created = Tag.get_or_create(self.tester, 'non-existing-autocreated-tag')

        self.assertNotEqual(tag.pk, self.existing_tag.pk)
        self.assertTrue(created)


class TestTagsWithoutPermission(LoggedInTestCase):
    """Test Tag usage/autocreation without permission"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        remove_perm_from_user(cls.tester, 'management.add_tag')

        cls.existing_tag = TagFactory()

    def test_get_existing_tag(self):
        tag, created = Tag.get_or_create(self.tester, self.existing_tag.name)

        self.assertEqual(tag.pk, self.existing_tag.pk)
        self.assertFalse(created)

    def test_autocreate_new_tag(self):
        with self.assertRaises(Tag.DoesNotExist):
            Tag.get_or_create(self.tester, 'non-existing-tag-without-permission')
