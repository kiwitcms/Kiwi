# -*- coding: utf-8 -*-
import itertools

from tcms.core.db import SQLExecution


def create_group_by_dict(sql, params, key_func):
    """
    @param sql: the SQL query to execute
    @type sql: basestring
    @param params: parameters to bind with SQL
    @type params: list or tuple
    @param key_func: key function
    @type key_func: callable object
    @return: dict with SQL query results
    @:rtype: dict
    """
    result_set = SQLExecution(sql, params)
    group_data = itertools.groupby(result_set.rows, key_func)
    return dict((key, [v for v in values]) for key, values in group_data)
