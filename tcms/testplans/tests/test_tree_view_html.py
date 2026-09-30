# -*- coding: utf-8 -*-
#
# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

"""
Tests for the Test Plan family tree.

Every Test Plan page renders the family tree via
:meth:`tcms.testplans.models.TestPlan.tree_view_html`, which relies on
:meth:`tcms.testplans.models.TestPlan.tree_as_list` returning the whole
family in depth first order, starting from the root of the tree.

``django-tree-queries`` declares the columns of its recursive CTE as
``char(1000)`` and ``tree_ordering`` grows by 20 characters per level. MariaDB
doesn't widen that type when the branches of the CTE are merged so deeper
trees are truncated, losing the depth first ordering, and cannot be saved at
all when ``sql_mode`` is strict. :data:`tcms.testplans.models.MAX_TREE_NODES`
is the number of TestPlans which fit on a single root to leaf path.

https://github.com/kiwitcms/Kiwi/issues/4334
"""

from http import HTTPStatus

from django.urls import reverse

from tcms.testplans.models import MAX_TREE_NODES, TestPlan
from tcms.tests import LoggedInTestCase, user_should_have_perm
from tcms.tests.factories import TestPlanFactory


class TestPlanFamilyTreeTest(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        user_should_have_perm(cls.tester, perm="testplans.view_testplan")

        # a tree as deep as the database can handle, one TestPlan per level
        cls.plan = TestPlanFactory()

        for _index in range(MAX_TREE_NODES - 1):
            cls.plan = TestPlanFactory(parent=cls.plan)

    def test_tree_as_list_is_in_depth_first_order(self):
        nodes = self.plan.tree_as_list()

        depths = []
        for node in nodes:
            depths.append(node.tree_depth)

        # one node per level, starting at the root of the tree
        self.assertEqual(depths, list(range(MAX_TREE_NODES)))

    def test_open_deeply_nested_test_plan(self):
        location = reverse("test_plan_url", args=[self.plan.pk])

        response = self.client.get(location)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_add_deeper_test_plan(self):
        if not TestPlan.tree_columns_are_truncated():
            self.skipTest("the tree columns are not truncated on this database")

        with self.assertRaisesRegex(
            RuntimeError,
            f"A TestPlan tree can have at most {MAX_TREE_NODES} TestPlans",
        ):
            TestPlanFactory(parent=self.plan)
