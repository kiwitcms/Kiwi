# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods, unused-argument

import factory
from factory.django import DjangoModelFactory

from tcms.tests.factories import BuildFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory


class BugFactory(DjangoModelFactory):

    class Meta:
        model = 'bugs.Bug'

    summary = factory.Sequence(lambda n: 'Bug %d' % n)
    reporter = factory.SubFactory(UserFactory)
    assignee = factory.SubFactory(UserFactory)
    product = factory.SubFactory(ProductFactory)
    version = factory.SubFactory(VersionFactory)
    build = factory.SubFactory(BuildFactory)
