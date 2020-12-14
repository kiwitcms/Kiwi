# coding: utf-8
import html

from modernrpc.handlers import JSONRPCHandler


class SafeJSONRPCHandler(JSONRPCHandler):
    @staticmethod
    def escape_dict(result_dict):
        for (key, value) in result_dict.items():
            if isinstance(value, str):
                result_dict[key] = html.escape(value)

    @staticmethod
    def escape_list(result_list):
        for (index, item) in enumerate(result_list):
            if isinstance(item, str):
                result_list[index] = html.escape(item)
            elif isinstance(item, dict):
                SafeJSONRPCHandler.escape_dict(item)

    def execute_procedure(self, name, args=None, kwargs=None):
        """
        HTML escape every string before returning it to
        the client, which may as well be the webUI. This will
        prevent XSS attacks for pages which display whatever
        is in the DB (e.g. tags, components)
        """
        result = super().execute_procedure(name, args, kwargs)

        if isinstance(result, str):
            result = html.escape(result)
        elif isinstance(result, dict):
            self.escape_dict(result)
        elif isinstance(result, list):
            self.escape_list(result)

        return result
