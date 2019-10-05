# -*- coding: utf-8 -*-

import io
import time
from mock import MagicMock

from attachments.models import Attachment
from attachments import views as attachment_views

from django.http import HttpRequest
from django.middleware.csrf import get_token
from django.db.models import FieldDoesNotExist

from tcms.management.models import Product
from tcms.core.utils import request_host_link


QUERY_DISTINCT = 1

ACCEPTABLE_BOOL_VALUES = ('0', '1', 0, 1, True, False)


def parse_bool_value(value):
    if value in ACCEPTABLE_BOOL_VALUES:
        if value == '0':
            return False
        if value == '1':
            return True
        return value
    raise ValueError('Unacceptable bool value.')


def pre_check_product(values):
    if isinstance(values, dict):
        if not values.get('product'):
            raise ValueError('No product given.')
        product_str = values['product']
    else:
        product_str = values

    if isinstance(product_str, str):
        if not product_str:
            raise ValueError('Got empty product name.')
        return Product.objects.get(name=product_str)
    if isinstance(product_str, int):
        return Product.objects.get(pk=product_str)
    raise ValueError('The type of product is not recognizable.')


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
    for field_name in fields:
        try:
            field = cls._meta.get_field(field_name)
            if field.is_relation and field.many_to_many:
                yield True
            else:
                if getattr(field, 'remote_field', None):
                    cls = field.remote_field.model
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
    return next(_lookup_fields_in_model(cls, fields), False) if fields else False


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
    for field in values.keys():
        if '__' in field:
            if _need_distinct_m2m_rows(cls, field.split('__')):
                flag = True
                break

    qs = cls.objects.filter(**values)
    if op_type == QUERY_DISTINCT:
        return qs.distinct() if flag else qs
    raise TypeError('Not implement op type %s' % op_type)


def distinct_filter(cls, values):
    return distinct_m2m_rows(cls, values, op_type=QUERY_DISTINCT)


def get_attachments_for(request, obj):
    host_link = request_host_link(request)
    result = []
    for attachment in Attachment.objects.attachments_for_object(obj):
        result.append({
            'pk': attachment.pk,
            'url': host_link + attachment.attachment_file.url,
            'owner_pk': attachment.creator.pk,
            'owner_username': attachment.creator.username,
            'date': attachment.created.isoformat(),
        })
    return result


def encode_multipart(csrf_token, filename, b64content):
    """
        Build a multipart/form-data body with generated random boundary
        suitable for parsing by django.http.request.HttpRequest and
        the parser classes related to it!

        .. note::

            ``\\r\\n`` are expected! Do not change!
    """
    boundary = '----------%s' % int(time.time() * 1000)
    data = ['--%s' % boundary]

    data.append('Content-Disposition: form-data; name="csrfmiddlewaretoken"\r\n')
    data.append(csrf_token)
    data.append('--%s' % boundary)

    data.append('Content-Disposition: form-data; name="attachment_file"; filename="%s"' % filename)
    data.append('Content-Type: application/octet-stream')
    data.append('Content-Transfer-Encoding: base64')
    data.append('Content-Length: %d\r\n' % len(b64content))
    data.append(b64content)

    data.append('--%s--\r\n' % boundary)
    return '\r\n'.join(data), boundary


def request_for_upload(user, filename, b64content):
    """
        Return a request object containing all fields necessary for file
        upload as if it was sent by the browser.
    """
    request = HttpRequest()
    request.user = user
    request.method = 'POST'
    request.content_type = 'multipart/form-data'
    # because attachment.views.add_attachment() calls messages.success()
    request._messages = MagicMock()

    data, boundary = encode_multipart(
        get_token(request),
        filename,
        b64content
    )

    request.META['CONTENT_TYPE'] = 'multipart/form-data; boundary=%s' % boundary
    request.META['CONTENT_LENGTH'] = len(data)
    request._stream = io.BytesIO(data.encode())

    # manually parse the input data and populate data attributes
    request._read_started = False
    request._load_post_and_files()
    request.POST = request._post
    request.FILES = request._files

    return request


def add_attachment(obj_id, app_model, user, filename, b64content):
    """
        High-level function which performs the attachment process
        by constructing an HttpRequest object and passing it to
        attachments.views.add_attachment() as if it came from the browser.
    """
    request = request_for_upload(user, filename, b64content)
    app, model = app_model.split('.')
    response = attachment_views.add_attachment(request, app, model, obj_id)
    if response.status_code == 404:
        raise Exception("Adding attachment to %s(%d) failed" % (app_model, obj_id))
