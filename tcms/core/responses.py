# -*- coding: utf-8 -*-

from functools import partial

from django import http


__all__ = ('HttpJSONResponse',
           'HttpJSONResponseBadRequest',
           'HttpJSONResponseServerError', )


MIMETYPE_JSON = 'application/json'

HttpJSONResponse = partial(http.HttpResponse, content_type=MIMETYPE_JSON)
HttpJSONResponseBadRequest = partial(http.HttpResponseBadRequest,
                                     content_type=MIMETYPE_JSON)
HttpJSONResponseServerError = partial(http.HttpResponseServerError,
                                      content_type=MIMETYPE_JSON)
