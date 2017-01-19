# -*- coding: utf-8 -*-
import json

from tcms.core.response import HttpJSONResponse

__all__ = (
    'AjaxResponseMixin',
)


class AjaxResponseCode:
    success = 0
    error = 1


class AjaxResponseMixin(object):
    errors = None
    result_code = AjaxResponseCode.success

    def update_errors(self, msg, errors=None):
        '''
        msg: an error message
        errors: a dictionary of errors, e.g., form.errors
        '''
        # once update_errors is called, set result_code
        self.result_code = AjaxResponseCode.error
        if errors is not None:
            self.errors = errors
        else:
            self.errors = msg

    def dumps(self, data):
        return json.dumps(data)

    def render_to_json(self, data):
        '''
        It is important to keep all the key names
        consistent in the context, because UI will
        have to rely on these names to access it.
        '''
        context = {
            'rc': self.result_code,
            'msg': self.errors,
            'data': data
        }
        return HttpJSONResponse(self.dumps(context))

    def ajax_response(self, context=None, **kwargs):
        if context is None:
            context = {}
        context.update(kwargs)
        return self.render_to_json(context)
