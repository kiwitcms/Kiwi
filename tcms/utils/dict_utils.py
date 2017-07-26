# -*- coding: utf-8 -*-


def create_dict_from_query(query, key_field, skip_others=False):
    """
        Group values based on a particular field.

        @param query: Django values() query, ordered by key_field
                or any other iterator that returns dicts
        @param key_field: field name by which to grup
        @param skip_others: if given the result will contain only the
                first record matching key_field. This is useful when
                we want to filter only the latest varsions of some
                records.

        @return: dict where keys are key_field values and
                 values are a list of the query records.
    """
    result_dict = {}
    for record in query:
        key_value = record[key_field]

        if key_value in result_dict:
            if not skip_others:
                result_dict[key_value].append(record)
        else:
            result_dict[key_value] = [record]

    return result_dict
