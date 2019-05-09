from django.db.models import Count
from django.utils.translation import ugettext_lazy as _
from modernrpc.core import rpc_method

from tcms.testcases.models import TestCase, TestCaseStatus


@rpc_method(name='Testing.breakdown')
def breakdown(query=None):
    """
    .. function:: XML-RPC Testing.breakdown(query)

        Perform a search and return the statistics for the selected test cases

        :param query: Field lookups for :class:`tcms.testcases.models.TestCase`
        :type query: dict
        :return: Object, containing the statistics for the selected test cases
        :rtype: dict
    """

    if query is None:
        query = {}

    test_cases = TestCase.objects.filter(**query).filter()

    manual_count = test_cases.filter(is_automated=False).count()
    automated_count = test_cases.filter(is_automated=True).count()
    count = {
        'manual': manual_count,
        'automated': automated_count,
        'all': manual_count + automated_count
    }

    priorities = _get_field_count_map(test_cases, 'priority', 'priority__value')
    categories = _get_field_count_map(test_cases, 'category', 'category__name')

    return {
        'count': count,
        'priorities': priorities,
        'categories': categories,
    }


def _get_field_count_map(test_cases, expression, field):
    confirmed = TestCaseStatus.get_confirmed()

    query_set_confirmed = test_cases.filter(
        case_status=confirmed
    ).values(field).annotate(
        count=Count(expression)
    )
    query_set_not_confirmed = test_cases.exclude(
        case_status=confirmed
    ).values(field).annotate(
        count=Count(expression)
    )
    return {
        confirmed.name: _map_query_set(query_set_confirmed, field),
        str(_('OTHER')): _map_query_set(query_set_not_confirmed, field)
    }


def _map_query_set(query_set, field):
    return {entry[field]: entry['count'] for entry in query_set}
