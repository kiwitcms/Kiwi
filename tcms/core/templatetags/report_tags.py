# -*- coding: utf-8 -*-
from django import template

register = template.Library()


@register.filter(name="percentage")
def percentage(fraction, population):
    try:
        value = (float(fraction) / float(population)) * 100
        return f"{value:.1f}%"
    except ZeroDivisionError:
        return "0%"
