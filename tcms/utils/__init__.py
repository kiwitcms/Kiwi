# -*- coding: utf-8 -*-

from django.apps import apps


def get_model(content_type):
    """Get model class from content type

    :param str content_type: content type in format app_label.model_name
    :return: model class
    """
    app_label, model_name = content_type.split('.')
    app_config = apps.get_app_config(app_label)
    return app_config.get_model(model_name)
