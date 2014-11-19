# -*- coding: utf-8 -*-

__all__ = ('HttpJSONResponse',
           'HttpJSONResponseBadRequest',
           'HttpJSONResponseServerError', )

from django.http import HttpResponse, HttpResponseBadRequest, \
    HttpResponseServerError

from tcms.search.forms import partial


MIMETYPE_JSON = 'application/json'

HttpJSONResponse = partial(HttpResponse, content_type=MIMETYPE_JSON)
HttpJSONResponseBadRequest = partial(HttpResponseBadRequest,
                                     content_type=MIMETYPE_JSON)
HttpJSONResponseServerError = partial(HttpResponseServerError,
                                      content_type=MIMETYPE_JSON)
