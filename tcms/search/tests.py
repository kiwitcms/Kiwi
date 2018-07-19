from django import test
from tcms.search.advanced_search import _sum_orm_queries
from tcms.search.query import SmartDjangoQuery
from tcms.testcases.models import TestCase
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestRun


class TestSumOrmQueries(test.TestCase):

    def test_with_invalid_target(self):

        with self.assertRaises(ValueError, msg='Invalid target'):
            _sum_orm_queries(SmartDjangoQuery({}, TestPlan.__name__),
                             SmartDjangoQuery({}, TestCase.__name__),
                             SmartDjangoQuery({}, TestRun.__name__),
                             'INVALID_TARGET')
