# -*- coding: utf-8 -*-
#  pylint: disable=too-few-public-methods

import re
from django.conf import settings


def is_int(string):
    return re.compile(r'^\d+$').match(string) is not None


def string_to_list(strs, spliter=','):
    """Convert the string to list"""
    if isinstance(strs, list):
        str_list = (str(item).strip() for item in strs)
    elif isinstance(strs, str) and strs.find(spliter):
        str_list = (str(item).strip() for item in strs.split(spliter))
    else:
        str_list = (strs,)
    return [s for s in str_list if s]


def form_errors_to_list(form):
    """
    Convert errors of form to list
    Use for Ajax.Request response
    """
    return [(k, str(v[0])) for k, v in form.errors.items()]


def calc_percent(dividend, divisor):
    if not dividend or not divisor:
        return 0

    return float(dividend) / divisor * 100


def request_host_link(request=None, domain_name=None):
    if request is None and settings.DEBUG is False:
        # default to https if in production and we don't know
        # what else to do
        protocol = 'https://'
    elif request and request.is_secure():
        protocol = 'https://'
    else:
        protocol = 'http://'

    if not domain_name:
        domain_name = request.get_host()

    return protocol + domain_name


def clean_request(request, keys=None):
    """
    Clean the request strings
    """
    request_contents = request.GET.copy()
    if not keys:
        keys = request_contents.keys()
    cleaned_request = {}
    for key in keys:
        key = str(key)
        if request_contents.get(key):
            if key == 'order_by' or key == 'from_plan':
                continue

            value = request.GET[key]
            # Convert the value to be list if it's __in filter.
            if key.endswith('__in') and isinstance(value, str):
                value = string_to_list(value)
            cleaned_request[key] = value
    return cleaned_request


class QuerySetIterationProxy(object):
    '''Iterate a series of object and its associated objects at once

    This iteration proxy applies to this kind of structure especially.

    Group       Properties          Logs
    -------------------------------------------------
    group 1     property 1          log at Mon.
                property 2          log at Tue.
                property 3          log at Wed.
    -------------------------------------------------
    group 2     property 4          log at Mon.
                property 5          log at Tue.
                property 6          log at Wed.
    -------------------------------------------------
    group 3     property 7          log at Mon.
                property 8          log at Tue.
                property 9          log at Wed.

    where, in each row of the table, one or more than one properties and logs
    to be shown along with the group.
    '''

    def __init__(self, iterable, associate_name=None, **associated_data):
        '''Initialize proxy

        Arguments:
        - iterable: an iterable object representing the main set of objects.
        - associate_name: the attribute name of each object within iterable,
          from which value is retrieve to get associated data from
          associate_data. Default is 'pk'.
        - associate_data: the associated data, that contains all data for each
          item in the set referenced by iterable. You can pass mulitple
          associated data as the way of Python **kwargs. The associated data
          must be grouped by the value of associate_name.
        '''
        self._iterable = iter(iterable)
        self._associate_name = associate_name
        if self._associate_name is None:
            self._associate_name = 'pk'
        self._associated_data = associated_data

    def __iter__(self):
        return self

    def __next__(self):
        next_one = next(self._iterable)
        for name, lookup_table in self._associated_data.items():
            setattr(next_one,
                    name,
                    lookup_table.get(
                        getattr(next_one, self._associate_name, None),
                        ()))
        return next_one


class DataTableResult(object):
    """Paginate and order queryset for rendering DataTable response"""

    def __init__(self, request_data, queryset, column_names):
        self.queryset = queryset
        self.request_data = request_data
        self.column_names = column_names

    def _iter_sorting_columns(self):
        number_of_sorting_cols = int(self.request_data.get('iSortingCols', 0))
        for idx_which_column in range(number_of_sorting_cols):
            sorting_col_index = int(
                self.request_data.get('iSortCol_{}'.format(idx_which_column),
                                      0))

            sortable_key = 'bSortable_{}'.format(sorting_col_index)
            sort_dir_key = 'sSortDir_{}'.format(idx_which_column)

            sortable = self.request_data.get(sortable_key, 'false')
            if sortable == 'false':
                continue

            sorting_col_name = self.column_names[sorting_col_index]
            sorting_direction = self.request_data.get(sort_dir_key, 'asc')
            yield sorting_col_name, sorting_direction

    def _sort_result(self):
        sorting_columns = self._iter_sorting_columns()
        order_fields = ['-{}'.format(col_name) if direction == 'desc' else col_name
                        for col_name, direction in sorting_columns]
        if order_fields:
            self.queryset = self.queryset.order_by(*order_fields)

    def _paginate_result(self):
        display_length = int(self.request_data.get('iDisplayLength', settings.DEFAULT_PAGE_SIZE))
        display_start = int(self.request_data.get('iDisplayStart', 0))
        display_end = display_start + display_length
        self.queryset = self.queryset[display_start:display_end]

    def get_response_data(self):
        total_records = total_display_records = self.queryset.count()

        self._sort_result()
        self._paginate_result()

        return {
            'sEcho': int(self.request_data.get('sEcho', 0)),
            'iTotalRecords': total_records,
            'iTotalDisplayRecords': total_display_records,
            'querySet': self.queryset,
        }
