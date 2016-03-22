# -*- coding: utf-8 -*-

import re
from django.db.models import Count, FieldDoesNotExist

from tcms.management.models import Product


COUNT_DISTINCT = 0
QUERY_DISTINCT = 1

ACCEPTABLE_BOOL_VALUES = ('0', '1', 0, 1, True, False)


def parse_bool_value(value):
    if value in ACCEPTABLE_BOOL_VALUES:
        if value is '0':
            return False
        elif value is '1':
            return True
        else:
            return value
    else:
        raise ValueError('Unacceptable bool value.')


def pre_check_product(values):
    if isinstance(values, dict):
        if not values.get('product'):
            return
        product_str = values['product']
    else:
        product_str = values

    if not (isinstance(product_str, str) or isinstance(product_str, int)):
        raise ValueError('The type of product is not recognizable.')

    try:
        product_id = int(product_str)
        return Product.objects.get(id=product_id)
    except ValueError:
        return Product.objects.get(name=product_str)


def pre_process_ids(value):
    if isinstance(value, list):
        return [isinstance(c, int) and c or int(c.strip()) for c in value if c]

    if isinstance(value, str):
        return [int(c.strip()) for c in value.split(',') if c]

    if isinstance(value, int):
        return [value]

    raise TypeError('Unrecognizable type of ids')


def compare_list(src_list, dest_list):
    return list(set(src_list) - set(dest_list))


def _lookup_fields_in_model(cls, fields):
    """Lookup ManyToMany fields in current table and related tables. For
    distinct duplicate rows when using inner join

    @param cls: table model class
    @type cls: subclass of django.db.models.Model
    @param fields: fields in where condition.
    @type fields: list
    @return: whether use distinct or not
    @rtype: bool

    Example:
        cls is TestRun (<class 'tcms.testruns.models.TestRun'>)
        fields is 'plan__case__is_automated'
                    |     |         |----- Normal Field in TestCase
                    |     |--------------- ManyToManyKey in TestPlan
                    |--------------------- ForeignKey in TestRun

    1. plan is a ForeignKey field of TestRun and it will trigger getting the
    related model TestPlan by django orm framework.
    2. case is a ManyToManyKey field of TestPlan and it will trigger using
    INNER JOIN to join TestCase, here will be many duplicated rows.
    3. is_automated is a local field of TestCase only filter the rows (where
    condition).

    So this method will find out that case is a m2m field and notice the
    outter method use distinct to avoid duplicated rows.
    """
    for field in fields:
        try:
            field_info = cls._meta.get_field_by_name(field)
            if field_info[-1]:
                yield True
            else:
                if getattr(field_info[0], 'related', None):
                    cls = field_info[0].related.parent_model
        except FieldDoesNotExist:
            pass


def _need_distinct_m2m_rows(cls, fields):
    """Check whether the query string has ManyToMany field or not, return
    False if the query string is empty.

    @param cls: table model class
    @type cls: subclass of django.db.models.Model
    @param fields: fields in where condition.
    @type fields: list
    @return: whether use distinct or not
    @rtype: bool
    """
    return next(_lookup_fields_in_model(cls, fields), False) \
        if fields else False


def distinct_m2m_rows(cls, values, op_type):
    """By django model field looking up syntax, loop values and check the
    condition if there is a multi-tables query.

    @param cls: table model class
    @type cls: subclass of django.db.models.Model
    @param values: fields in where condition.
    @type values: dict
    @return: QuerySet
    @rtype: django.db.models.query.QuerySet
    """
    flag = False
    for field in values.iterkeys():
        if '__' in field:
            if _need_distinct_m2m_rows(cls, field.split('__')):
                flag = True
                break

    qs = cls.objects.filter(**values)
    if op_type == COUNT_DISTINCT:
        return qs.aggregate(Count('pk', distinct=True))['pk__count'] if flag \
            else qs.count()
    elif op_type == QUERY_DISTINCT:
        return qs.distinct() if flag else qs
    else:
        raise TypeError('Not implement op type %s' % op_type)


def distinct_count(cls, values):
    return distinct_m2m_rows(cls, values, op_type=COUNT_DISTINCT)


def distinct_filter(cls, values):
    return distinct_m2m_rows(cls, values, op_type=QUERY_DISTINCT)


class Comment(object):
    def __init__(self, request, content_type, object_pks, comment=None):
        self.request = request
        self.content_type = content_type
        self.object_pks = object_pks
        self.comment = comment

    def add(self):
        import time
        from django.contrib import comments
        from django_comments import signals
        from django.db import models

        comment_form = comments.get_form()

        try:
            model = models.get_model(*self.content_type.split('.', 1))
            targets = model._default_manager.filter(pk__in=self.object_pks)
        except:
            raise

        for target in targets.iterator():
            d_form = comment_form(target)
            timestamp = str(time.time()).split('.')[0]
            object_pk = str(target.pk)
            data = {
                'content_type': self.content_type,
                'object_pk': object_pk,
                'timestamp': timestamp,
                'comment': self.comment
            }
            security_hash_dict = {
                'content_type': self.content_type,
                'object_pk': object_pk,
                'timestamp': timestamp
            }
            data['security_hash'] = d_form.generate_security_hash(
                **security_hash_dict)
            form = comment_form(target, data=data)

            # Response the errors if got
            if not form.is_valid():
                return form.errors

            # Otherwise create the comment
            comment = form.get_comment_object()
            comment.ip_address = self.request.META.get("REMOTE_ADDR", None)
            if self.request.user.is_authenticated():
                comment.user = self.request.user

            # Signal that the comment is about to be saved
            signals.comment_will_be_posted.send(
                sender=comment.__class__,
                comment=comment,
                request=self.request
            )

            # Save the comment and signal that it was saved
            comment.save()
            signals.comment_was_posted.send(
                sender=comment.__class__,
                comment=comment,
                request=self.request
            )

        return


estimated_time_re = re.compile(r'^(\d+[d])?(\d+[h])?(\d+[m])?(\d+[s])?$')


def pre_process_estimated_time(value):
    '''pre process estiamted_time.

    support value - HH:MM:SS & xdxhxmxs
    return xdxhxmxs
    '''
    if isinstance(value, str):
        match = estimated_time_re.match(value.replace(' ', ''))
        if match:
            return value
        else:
            # FIXME: missed validation to invalid value in HH:MM:SS format.
            # for example: sfsdfs:sfwerwe:rerwerwe
            raw_estimated_time = value.split(':')

            if len(raw_estimated_time) == 3:
                hours, minutes, seconds = raw_estimated_time
                return '{0}h{1}m{2}s'.format(hours, minutes, seconds)
            else:
                raise ValueError('Invaild estimated_time format.')
    else:
        raise ValueError('Invaild estimated_time format.')
