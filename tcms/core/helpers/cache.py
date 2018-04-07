# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache


def cached_entities(content_type_name):
    """
    Some entities are frequently used.\n
    Cache them for reuse.\n
    Retrieve using model names.
    """
    content_type_key = 'ctt_type_' + content_type_name
    content_type = cache.get(content_type_key)
    if not content_type:
        content_type = ContentType.objects.get(model__iexact=content_type_name)
        cache.set(content_type_key, content_type)
    model_class = content_type.model_class()
    key = 'cached_' + content_type_name
    entities = cache.get(key)
    if not entities:
        entities = model_class.objects.all()
        cache.set(key, entities)
    return entities
