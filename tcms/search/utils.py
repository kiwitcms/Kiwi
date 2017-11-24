# -*- coding: utf-8 -*-

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache


def cached_entities(ctype_name):
    """
    Some entities are frequently used.\n
    Cache them for reuse.\n
    Retrieve using model names.
    """
    ctype_key = 'ctt_type_' + ctype_name
    c_type = cache.get(ctype_key)
    if not c_type:
        c_type = ContentType.objects.get(model__iexact=ctype_name)
        cache.set(ctype_key, c_type)
    model_class = c_type.model_class()
    key = 'cached_' + ctype_name
    entities = cache.get(key)
    if not entities:
        entities = model_class._default_manager.all()
        cache.set(key, entities)
    return entities
