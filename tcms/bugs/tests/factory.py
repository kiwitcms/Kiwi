# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods, unused-argument

import factory
from factory.django import DjangoModelFactory

from tcms.tests.factories import (
    BuildFactory,
    ProductFactory,
    UserFactory,
    VersionFactory,
)


class BugFactory(DjangoModelFactory):
    class Meta:
        model = "bugs.Bug"

    summary = factory.Sequence(lambda n: f"Bug {n}")
    reporter = factory.SubFactory(UserFactory)
    assignee = factory.SubFactory(UserFactory)
    product = factory.SubFactory(ProductFactory)
    version = factory.SubFactory(VersionFactory)
    build = factory.SubFactory(BuildFactory)
