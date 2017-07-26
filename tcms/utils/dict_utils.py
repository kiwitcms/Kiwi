# -*- coding: utf-8 -*-
import itertools

from tcms.core.db import SQLExecution


def create_group_by_dict(sql, params, key_func):
    '''

    @param sql: the SQL query to execute
    @type sql: basestring
    @param params: parameters to bind with SQL
    @type params: list or tuple
    @param key_func: key function
    @type key_func: callable object
    @return: dict with SQL query results
    @:rtype: dict
    '''
    result_set = SQLExecution(sql, params)
    group_data = itertools.groupby(result_set.rows, key_func)
    return dict((key, [v for v in values]) for key, values in group_data)

def create_dict_from_query(query, key_field):
    """
        Group values based on a particular field.

        @param query: Django values() query, ordered by key_field
        @param key_field: field name by which to grup

        @return: dict where keys are key_field values and
                 values are a list of the query records.
    """
    result_dict = {}
    for record in query:
        key_value = record[key_field]

        if key_value in result_dict:
            result_dict[key_value].append(record)
        else:
            result_dict[key_value] = [record]

    return result_dict
