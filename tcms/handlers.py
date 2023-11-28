# coding: utf-8
import html
from datetime import timedelta

from modernrpc.handlers import JSONRPCHandler, XMLRPCHandler
from modernrpc.handlers.base import BaseResult, SuccessResult
from modernrpc.handlers.jsonhandler import JsonResult, JsonSuccessResult


class KiwiTCMSJsonRpcHandler(JSONRPCHandler):
    @staticmethod
    def escape_dict(result_dict):
        for key, value in result_dict.items():
            if isinstance(value, str):
                result_dict[key] = html.escape(value)
            elif isinstance(value, timedelta):
                result_dict[key] = value.total_seconds()

    @staticmethod
    def escape_list(result_list):
        for index, item in enumerate(result_list):
            if isinstance(item, str):
                result_list[index] = html.escape(item)
            elif isinstance(item, timedelta):
                result_list[index] = item.total_seconds()
            elif isinstance(item, dict):
                __class__.escape_dict(item)

    def dumps_result(self, result: JsonResult) -> str:
        if isinstance(result, JsonSuccessResult):
            if isinstance(result.data, str):
                result.data = html.escape(result.data)
            elif isinstance(result.data, timedelta):
                result.data = result.data.total_seconds()
            elif isinstance(result.data, dict):
                self.escape_dict(result.data)
            elif isinstance(result.data, list):
                self.escape_list(result.data)

        return super().dumps_result(result)


class KiwiTCMSXmlRpcHandler(XMLRPCHandler):
    @staticmethod
    def escape_dict(result_dict):
        for key, value in result_dict.items():
            if isinstance(value, timedelta):
                result_dict[key] = value.total_seconds()

    @staticmethod
    def escape_list(result_list):
        for index, item in enumerate(result_list):
            if isinstance(item, timedelta):
                result_list[index] = item.total_seconds()
            elif isinstance(item, dict):
                __class__.escape_dict(item)

    def dumps_result(self, result: BaseResult) -> str:
        if isinstance(result, SuccessResult):
            if isinstance(result.data, timedelta):
                result.data = result.data.total_seconds()
            elif isinstance(result.data, dict):
                self.escape_dict(result.data)
            elif isinstance(result.data, list):
                self.escape_list(result.data)

        return super().dumps_result(result)
